# 从零手搓 Transformer：英文→中文翻译全流程实战

> 📦 源码仓库：[JiangYuxin-Jim/Transformer-pytorch](https://github.com/JiangYuxin-Jim/Transformer-pytorch)
> 🧪 定位：把 2026-10-26 学的 Transformer 架构，从「公式和示意图」变成「一套能跑通、能量化的代码」
> 🗓️ 完成时间：2026-10-28

---

## 0. 一句话总结

**这不是调 API 做翻译，而是把《Attention Is All You Need》用 PyTorch 逐层手写出来**：约 1500 行代码，从语料清洗、BPE 训练、Encoder-Decoder 建模、Noam 优化器训练，到 Beam Search 解码，最后用 SacreBLEU 量化出一个可比的分数（`best_bleu_26.30.pth`）。

关键认知升级：**Transformer 不是"背下来的结构图"，而是一串可以被任意改动的张量形状变换**——写不出来，就说明还没真懂。

---

## 1. 先看全景：一条完整的 MT 流水线

```
原始语料（json 平行句对）
   ↓ get_corpus.py            合并 train/dev/test → corpus.en / corpus.ch
   ↓ analyze_corpus.py        行数/字符数/对齐校验
   ↓ tokenizer/tokenize.py    SentencePiece 训练 eng.model / chn.model（BPE·32k）
   ↓ tools/data_loader.py     MTDataset → Batch（src / trg / trg_y / 三种 mask）
   ↓ model/tf_model.py        手搓 Transformer（Embedding→Encoder×6→Decoder×6→Generator）
   ↓ main.py                  Noam 优化器 + label-wise 交叉熵 + 每 epoch 用 Beam Search 算 BLEU
   ↓ beam_decoder.py          beam_size=3 的批内束搜索（含"已完成句子提前退出"优化）
   ↓ translate.py             加载权重 → 交互式单句翻译
```

### 项目骨架（真实文件职责）

| 文件 | 行数 | 职责 |
|------|------|------|
| `config.py` | 84 | 所有超参集中管理（模型/词表/训练/解码/设备） |
| `model/tf_model.py` | 330 | **核心**：Embedding·PositionalEncoding·MHA·LayerNorm·FFN·Sublayer·Encoder·Decoder·Generator·make_model |
| `model/train_utils.py` | 119 | `MultiGPULossCompute`（分块损失+梯度聚合）· `NoamOpt`（warmup 学习率） |
| `beam_decoder.py` | 228 | `Beam` 状态类 + `beam_search` 批处理解码器 |
| `tools/data_loader.py` | 159 | `subsequent_mask`· `Batch`· `MTDataset` |
| `tools/tokenizer_utils.py` | 36 | 中英 SentencePiece 加载 |
| `main.py` | 172 | `run_epoch`· `train`· `evaluate`（BLEU）· `test` |
| `translate.py` | 99 | 单句推理入口 |
| `data/*.py` | ~100 | 语料合并 / 统计 / 分词器训练 |

---

## 2. 超参配置：照 paper base 版本，只改了两处

```python
d_model = 512;  n_heads = 8;  n_layers = 6
d_k = 64;  d_v = 64;  d_ff = 2048;  dropout = 0.1
src_vocab_size = tgt_vocab_size = 32000
padding_idx = 0;  bos_idx = 2;  eos_idx = 3
batch_size = 32;  epoch_num = 3;  lr = 3e-4
max_len = 60;  beam_size = 3
```

**⚠️ 两处务实改动（比 paper 小，是"能跑完"的关键）**：

| 项 | paper | 本项目 | 原因 |
|----|--------|--------|------|
| 层数 N | 6 enc + 6 dec ✅ 一致 | 6 / 6 | 没缩水 |
| 序列长度 | 训练按 batch 动态 | `max_len=60` 解码上限 | 中文译文比英文短，60 够用 |
| dropout 位置 | 每子层后 + PE + attention | 每子层后 + PE + attention ✅ | 一致 |
| FFN 激活 | ReLU | ReLU | 没用 GELU/GLU（现代 LLM 才换） |

> 💡 **`lr = 3e-4` 其实是个"摆设"**：NoamOpt 会覆盖所有 param_group 的 lr，真实学习率完全由 `factor / model_size / warmup` 决定。这是新手常见的困惑点。

### 特殊 token 的 id 约定（必须自己对齐）

`pad=0, unk=1, bos=2, eos=3`

这个约定在 **三处** 必须同时一致，否则训练直接崩：
1. `tokenize.py` 训练时显式传 `--pad_id=0 --unk_id=1 --bos_id=2 --eos_id=3`
2. `config.py` 的常量
3. `data_loader.py` 里用 `sp.pad_id()/bos_id()/eos_id()` 动态取值 + `CrossEntropyLoss(ignore_index=0)`

---

## 3. 数据层：容易被忽略但决定成败

### 3.1 语料来源与规模

- 平行语料 252,777 对（train + dev + test）
- `get_corpus.py` 把三份 json 合并成 `corpus.en` / `corpus.ch` 两个对齐的行文件
- `analyze_corpus.py` 做**行数对齐校验**（`✓ 中英文文件行数匹配`）—— 平行语料最容易出的就是这个错，错一行之后全错位

### 3.2 分词器：中英各一个 BPE，32k

```python
# 英文：character_coverage=1.0（字符集小，全覆盖）
# 中文：character_coverage=0.9995（推荐值，极少数生僻字映射 <unk>）
spm.SentencePieceTrainer.Train(
    '--input=corpus.en --model_prefix=eng --vocab_size=32000 '
    '--model_type=bpe --character_coverage=1.0 '
    '--pad_id=0 --unk_id=1 --bos_id=2 --eos_id=3')
```

**为什么中英分词器要分开训？**
词汇分布完全不同——中文 BPE 学到的是"词/字块"，英文学到的是"子词词缀"。共用一个词表会互相挤占 32k 的预算。

### 3.3 Batch：一次搞定三种 mask（这是最容易写错的地方）

```python
self.src_mask = (src != pad).unsqueeze(-2)          # 1×seq → padding mask

if trg is not None:
    self.trg   = trg[:, :-1]                        # 输入：BOS ... 倒数第二个
    self.trg_y = trg[:, 1:]                         # 标签：第一个 ... EOS
    self.trg_mask = self.make_std_mask(self.trg, pad)
    self.ntokens = (self.trg_y != pad).data.sum()    # 损失归一化用的有效 token 数
```

```python
@staticmethod
def make_std_mask(tgt, pad):
    tgt_mask = (tgt != pad).unsqueeze(-2)                         # padding mask
    return tgt_mask & subsequent_mask(tgt.size(-1)).type_as(...)  # & 因果 mask
```

**三种 mask 对照表**（必须记牢）：

| mask | 形状 | 作用 | 用在哪 |
|------|------|------|--------|
| `src_mask` | `[B, 1, S]` | 屏蔽源句 padding | Encoder 自注意力 + Decoder 交叉注意力 |
| `tgt_mask` | `[B, L, L]` | padding **&** 因果 | Decoder 自注意力 |
| `subsequent_mask` | `[1, L, L]` | 上三角为 False（看不到未来） | 训练/推理的解码自注意力 |

> ⚠️ **符号方向别搞反**：`attention()` 里是 `scores.masked_fill(mask == 0, -1e9)`，所以 mask 为 `True` 的位置是**允许看**的。`subsequent_mask` 用 `np.triu(..., k=1) == 0` 得到的正是「下三角 + 对角线为 True」。

**Teacher Forcing 体现在两行代码里**：`trg` 和 `trg_y` 是同一句错位一格——输入真实答案的前缀，预测下一个字，这是训练阶段并行化的前提（一次前向出整个序列的预测）。

---

## 4. 模型层：手搓 Transformer 逐块拆解

### 4.1 Embedding —— 为什么乘 √d_model

```python
return self.lut(x) * math.sqrt(self.d_model)
```
乘 √512 是为了让词向量和位置编码的**数值量级匹配**。位置编码的值域在 [-1, 1]，词向量初始化后是 N(0, 1/√d) 量级，不缩放的话位置信息会被淹没。

### 4.2 位置编码 —— 用 exp/log 代替幂运算

```python
div_term = torch.exp(torch.arange(0., d_model, 2) * -(math.log(10000.0) / d_model))
pe[:, 0::2] = torch.sin(position * div_term)   # 偶数维 → sin
pe[:, 1::2] = torch.cos(position * div_term)   # 奇数维 → cos
self.register_buffer('pe', pe)                 # buffer：不参与训练，跟着 .to(device) 走
```

**两个工程细节**：
1. `exp(-log(10000)/d * 2i)` 数值更稳，避免 `1/(10000^(2i/d))` 的浮点下溢
2. `register_buffer` 而不是 `nn.Parameter`——它是常量，不更新，但要随模型迁移设备

### 4.3 Scaled Dot-Product Attention —— 五行核心

```python
scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)
if mask is not None:
    scores = scores.masked_fill(mask == 0, -1e9)
p_attn = F.softmax(scores, dim=-1)
if dropout is not None:
    p_attn = dropout(p_attn)
return torch.matmul(p_attn, value), p_attn
```

- **除以 √d_k**：点积随维度增长方差变大，不缩放的话 softmax 会饱和成 one-hot，梯度消失
- **返回 attention 矩阵**：方便事后做可视化/调试（`self.attn` 被存下来）

### 4.4 Multi-Head Attention —— 拆分、并行、拼回

```python
query, key, value = [l(x).view(nbatches, -1, self.h, self.d_k).transpose(1, 2)
                     for l, x in zip(self.linears, (query, key, value))]
x, self.attn = attention(query, key, value, mask, self.dropout)
x = x.transpose(1, 2).contiguous().view(nbatches, -1, self.h * self.d_k)
return self.linears[-1](x)
```

形状变化记一遍就不会忘：
`[B, L, 512]` → `view` → `[B, L, 8, 64]` → `transpose` → `[B, 8, L, 64]` → attention → `[B, 8, L, 64]` → `transpose + view` → `[B, L, 512]` → `W_O`

`mask.unsqueeze(1)` 把 `[B, 1, L]` 变 `[B, 1, 1, L]`，好让广播到 `[B, 8, L, L]`——**这一步漏了会直接报 shape 错误**。

### 4.5 LayerNorm —— 手写而不是 `nn.LayerNorm`

```python
mean = x.mean(-1, keepdim=True)
std  = x.std(-1, keepdim=True)
return self.a_2 * (x - mean) / torch.sqrt(std ** 2 + self.eps) + self.b_2
```
按**最后一维**（特征维）归一化，每个 token 独立归一化，与 batch 大小无关——这就是为什么 Transformer 对 batch size 不敏感，而 BatchNorm 不行。

### 4.6 子层连接：**Post-LN** —— 与现在的 LLM 相反！

```python
def forward(self, x, sublayer):
    return x + self.dropout(sublayer(self.norm(x)))   # norm 在前，残差在外 → Post-LN
```

| 结构 | 公式 | 特点 |
|------|------|------|
| **Post-LN（本项目/原始 paper）** | `x + Dropout(Sublayer(Norm(x)))` | 输出未归一化，深层训练不稳，**必须 warmup** |
| Pre-LN（现代 LLM：GPT/Llama） | `x + Sublayer(Norm(x))` 且最后再 Norm 一次 | 梯度更稳，可去 warmup，能堆更深 |

> 💡 **这解释了为什么论文必须用 warmup**：Post-LN 的残差主干方差随层数累积，一上来大学习率必炸。Noam 的 `warmup=10000` 步正是给 Post-LN 打的补丁。

### 4.7 Encoder / Decoder / Generator

```python
# EncoderLayer
x = self.sublayer[0](x, lambda x: self.self_attn(x, x, x, mask))  # Q=K=V
return self.sublayer[1](x, self.feed_forward)

# DecoderLayer：三层子层，注意 Q 的来源不同！
x = self.sublayer[0](x, lambda x: self.self_attn(x, x, x, tgt_mask))   # 自注意力：Q=K=V=decoder hidden
x = self.sublayer[1](x, lambda x: self.src_attn(x, m, m, src_mask))    # 交叉注意力：Q=decoder, K=V=encoder
return self.sublayer[2](x, self.feed_forward)

# Generator
return F.log_softmax(self.proj(x), dim=-1)   # 输出 log 概率，配合 NLLLoss
```

**Encoder-Decoder 的信息流**：`memory = encoder(src_embed(src), src_mask)`，Decoder 每一层都去和这份 memory 做一次交叉注意力——**这是整个架构里"目标语言看源语言"的唯一通道**。

### 4.8 `make_model` —— 组装 + Xavier 初始化

```python
for p in model.parameters():
    if p.dim() > 1:
        nn.init.xavier_uniform_(p)     # 只初始化权重矩阵，跳过 bias 和 LayerNorm 的 a_2/b_2
```
`clones()` 用 `copy.deepcopy` 而不是共享引用——**6 层参数各自独立**（`nn.ModuleList` 才能被 optimater 看见）。

---

## 5. 训练：损失、优化器、BLEU 三重把关

### 5.1 损失：label-wise 交叉熵 + sum 后归一化

```python
criterion = nn.CrossEntropyLoss(ignore_index=0, reduction='sum')
# 每个 batch：loss = sum_loss / batch.ntokens  （按有效 token 数归一化）
```
用 `sum` 而不是 `mean` 是因为要**跨 GPU 分块聚合**时，mean 的权重不对；统一在最外层按 `ntokens` 归一化才能得到「每 token 平均 loss」。

### 5.2 Noam 学习率：warmup + 逆平方根衰减

```python
rate = factor * (model_size ** (-0.5) * min(step ** (-0.5), step * warmup ** (-1.5)))
# factor=1, model_size=512, warmup=10000, Adam(betas=(0.9, 0.98), eps=1e-9)
```

**两段曲线**：
- `step < warmup`：`step * warmup^-1.5` 线性升温 ← **给 Post-LN 预热**
- `step > warmup`：`step^-0.5` 逆平方根衰减 ← 越训练越小，后期精调

小细节：`get_std_opt` 里 Adam 的 `lr=0`，因为真实 lr 每个 step 由 NoamOpt 覆写；`eps` 从默认 `1e-8` 改成 `1e-9`，避免小梯度被吞。

### 5.3 `MultiGPULossCompute`：分块过 Generator 省显存

**为什么要 chunk？**
`Generator` 输出是 `[B, L, 32000]`，batch=32、len=60 时就是 200 万个 float，加上 log_softmax 的中间变量极易 OOM（论文级大词表下更夸张）。所以：

```python
for i in range(0, out_scatter[0].size(1), chunk_size):   # 沿序列维按 5 切
    out_column = o[:, i:i+chunk_size]
    gen = parallel_apply(generator, ...)                 # 只对这小块做 512→32000 投影
    loss = parallel_apply(criterion, ...)
    total += l_.data                                     # 只累加标量！
    if self.opt is not None:
        l_.backward()                                    # 反向到这一块 Transformer 输出
        out_grad[j].append(out_column[j][0].grad.data.clone())
# 循环结束后把各块梯度拼回去，对 Transformer 本体做一次完整 backward
o1.backward(gradient=gathered_grads)
self.opt.step(); self.opt.optimizer.zero_grad()
```

**核心技巧**：**逐块 backward 只拿标量，把每块对 `out` 的梯度 clone 存下来，最后拼成完整梯度一次性回传主干**。这样峰值显存只有「一小块 logits」而不是「全部 logits」。

> 👀 观察：本项目 `device_id = [0]`，其实只用了单卡，`nn.parallel` 这一套是多卡时代的遗产；理解它的价值在于**分块计算 + 梯度拼接**的思路，这在后来 FlashAttention / gradient checkpointing 里反复出现。

### 5.4 训练循环 + BLEU 早停

```python
train_loss = run_epoch(train, model_par, MultiGPULossCompute(..., optimizer))
dev_loss   = run_epoch(dev,   model_par, MultiGPULossCompute(..., None))   # opt=None → 不更新
bleu_score = evaluate(dev_data, model)   # ⚠️ dev 上跑一次完整 Beam Search 推理
if bleu_score > best_bleu_score:
    torch.save(model.state_dict(), f"{weights_folder}/best_bleu_{bleu_score:.2f}.pth")
```

**模型选择用的是 BLEU 而不是 dev_loss** —— 这是个重要经验：**交叉熵降了不代表译文更好**（teacher forcing 下模型可以只学会"抄前缀"），只有真正自回归解码出来的句子才可信。

代价是每个 epoch 要跑一次全量 Beam Search，evaluate 非常慢（见 8.3 的踩坑）。

---

## 6. 推理：Beam Search 手写全解析

`beam_size = 3`，批内并行，核心是 `Beam` 类维护每个句子的搜索状态。

### 6.1 Beam 状态四件套

```python
self.scores        # 当前 3 条候选的累积 log 概率
self.all_scores    # 历史分数（做长度归一化用）
self.prev_ks       # 每步的回溯指针：当前候选是从上一步哪条 beam 来的
self.next_ys       # 每步输出的 token：[BOS, PAD, PAD]
```

### 6.2 `advance` —— beam search 的唯一难点

```python
if len(self.prev_ks) > 0:
    beam_lk = word_logprob + self.scores.unsqueeze(1)     # 累积：本步 logP + 历史分数
else:
    beam_lk = word_logprob[0]                             # 第一步只有一条"前缀"

flat = beam_lk.view(-1)                                    # [beam × vocab] 拉平
best_scores, best_ids = flat.topk(self.size, ...)          # 全局取 top-k

prev_k = best_ids // num_words                             # 商 = 来自哪条 beam
self.prev_ks.append(prev_k)
self.next_ys.append(best_ids - prev_k * num_words)         # 余数 = 哪个词
```

**`//` 和 `%` 是 beam search 的精髓**：在一张 `[beam, vocab]` 的二维表里取全局 top-k，用整数除法反推来源 beam、用减法反推词 id——一次 `topk` 完成"选词 + 选路径"两件事。

### 6.3 `beam_search` 的三个批处理优化

1. **源端复制**：`src_enc.repeat(1, beam_size, 1)` → Encoder **只跑一次**，memory 复制 beam_size 份，而不是每条候选各编码一遍
2. **活跃句子过滤**（`collate_active_info`）：某句的 beam[0] 出 `<EOS>` 就标记 done，后续 step 把它从 batch 里剔除 → **短句先完成先退出，长句继续**，这是 batch 推理能大幅提速的关键
3. **回溯重建**（`get_hypothesis`）：从最后一步倒着走 `prev_ks`，得到完整 token 序列

### 6.4 训练 vs 推理的 mask 差异（易错点）

| | Encoder | Decoder 自注意力 |
|---|---|---|
| 训练 | `src_mask` 一次算好 | `tgt_mask`（padding + 因果） |
| 推理 | `src_mask` 同上 | `subsequent_mask(dec_seq.size(1))` 现场生成 |

**推理时没有 padding**（每句都精确到当前长度），且必须**每步重建完整因果 mask**：因为 `dec_seq` 长度在增长。这里 `model.decode()` 每步都对整段前缀重新跑一遍 Decoder（**没有 KV Cache**）——本项目是教学版，所以能接受；生产级实现会用 KV Cache 把复杂度从 O(L²) 降到 O(L)。

---

## 7. 结果与量化

- 最佳权重文件名：`best_bleu_26.30.pth` —— **验证集 BLEU ≈ 26.30**
- 评价工具：`sacrebleu.corpus_bleu(res, [refs], tokenize='zh')`

**BLEU 26.3 是什么水平？**
- 原始 paper 在 WMT14 EN-DE（约 450 万句）上做到 27.3，EN-FR 41.8
- 本项目语料 **25.3 万句（约 1/18）、只训 3 epoch**，拿到 26.3 属于**结构正确、训练充分的合理结果**——证明确实学到了翻译能力，而不只是语料复读
- 语境提示：BLEU 高≠译文好，它是 n-gram 精确率的几何平均，偏好"用词贴近参考"而非"语义正确"

**关键补充**：这次不仅跑通了模型，还**把模型自己翻译出来的结果做成了一份中文译文**——即"整个翻译代码流程"的最终产物。也就是说这条流水线同时是：一次架构复现 + 一个可用的英译中工具。

---

## 8. 踩坑清单（最值得记住的部分）

### 8.1 `main.py::test()` 的签名 bug
```python
def test(data, model, criterion):
    ...
    bleu_score = evaluate(data, model, 'test')   # ❌ evaluate 只接收 2 个参数
```
项目里 `run()` 的 `test(...)` 被注释掉了，所以一直没暴露。要跑测试集评估，得先把这行改成 `evaluate(data, model)`。**教训：注释掉的代码不是"对"的代码，是"没被验证过"的代码。**

### 8.2 `train()` 里 `os` 没导入
`if os.path.exists(old_model_path)` 依赖 `os`，而 `os` 只在 `__main__` 块里 `import`——模块级没有。删除旧最佳权重的分支一走到就 `NameError`。**教训：只在 `if __name__ == "__main__":` 里 import 的模块，在函数内是不可见的。**

### 8.3 `evaluate()` 极慢
每个 epoch 在 dev 全量上跑 Beam Search（无 KV Cache + Python 循环），dev 集几万句时一次评估能占掉大半个 epoch 的时间。**优化方向**：① 抽样评估（如 500 句）② 加 KV Cache ③ 减 beam_size 到 2。

### 8.4 设备适配：CUDA 硬编码
`config.py` 只有 `cuda` 和 `cpu` 两个分支，`MultiGPULossCompute` 直接依赖 `nn.parallel`。**Mac MPS 需要**：改 `device` 分支 + 去掉 `DataParallel`/`nn.parallel.replicate`（MPS 不支持多卡并行原语）。

### 8.5 词表与权重必须配套
换了模型结构或重新训了分词器，**旧权重全部作废**——因为 Embedding 行数/索引含义都变了。README 里专门标注"已提供的分词器与预训练权重应配套使用"就是这个原因。

### 8.6 3 个 epoch 是"跑完"而非"收敛"
`epoch_num = 3` 在这个数据量下只能算"验证流水线通了"。要真正提升 BLEU，最有效顺序是：**加数据 > 加 epoch > 调 beam_size > 换 Pre-LN/加 label smoothing**。

---

## 9. 和 paper 的差异清单（面试常问）

| 项 | 原论文 | 本项目 | 影响 |
|----|--------|--------|------|
| 结构 | Encoder-Decoder 6+6 | ✅ 一致 | — |
| 位置编码 | 正弦绝对位置 | ✅ 一致 | 没用 RoPE（现代 LLM 才换） |
| 归一化位置 | Post-LN | ✅ 一致（因此必须 warmup） | — |
| 优化器 | Adam + Noam（warmup=4000） | ✅ Adam + Noam（warmup=10000） | warmup 更长，更稳 |
| Label Smoothing | ε=0.1 | ❌ **未使用** | 本项目可提升点之一 |
| 分词 | BPE/word-piece 32k~37k | ✅ SentencePiece BPE 32k | 一致 |
| 解码 | Beam Search（长度惩罚） | ✅ Beam Search（**无长度惩罚**） | 短译文可能被偏好 |
| 训练数据 | WMT14 450万句 | 25万句 | BLEU 不可直接比 |
| 注意力优化 | 无 | ❌ 无 KV Cache（推理 O(L²)） | 教学取舍 |

---

## 10. 知识点串联：这次实战补上了什么

1. **和 hello-agents 第三章打通**：那时是"读架构图"，现在是"写架构"。Q/K/V 从"三个字母"变成三个 `nn.Linear`；"因果掩码"从"一个概念"变成 `np.triu(...) == 0` 的布尔矩阵。

2. **和 09 章上下文工程打通**：当时说过 **"n² 注意力 + softmax 归一化 → 上下文越长信息越稀释"**。写完代码才真正体会到这个因果链：`p_attn` 每行和恒为 1（`F.softmax(dim=-1)` 保证），序列翻倍则候选位置翻倍，每份信息分到的概率必然下降。**这就是"上下文腐蚀"的代码级证据。**

3. **和 LangChain/LangGraph 对照**：那边是"用别人的模型 + 编排"，这边是"造模型"。看到 `model.decode()` 每步重跑全前缀，才明白为什么 KV Cache 是 LLM 推理系统的第一优化项（也是为什么 Prompt 前缀能缓存省钱——同一回事的两端）。

4. **新建立的直觉**：
   - **Train / Eval 的差别不只是 `no_grad()`**：一个是 teacher forcing 并行喂答案，一个是自回归一步步猜——两套完全不同的执行路径，`evaluate()` 必须自己实现 Beam Search 而不是复用 forward
   - **模型选择的度量要贴近任务**：BLEU 选模型 > loss 选模型
   - **手写一遍才能发现"框架帮你做了什么"**：`nn.MultiheadAttention`、`nn.Transformer` 把这 330 行浓缩成两个类，代价是所有 shape 逻辑都变成黑盒

---

## 11. 下一步可做的改进

- [ ] 补 **Label Smoothing（ε=0.1）** —— 最小改动，通常 +0.5~1 BLEU
- [ ] 加 **KV Cache** —— 推理提速 5~10 倍，也是理解现代推理引擎的入口
- [ ] Beam Search 加 **长度惩罚**（`length_penalty = ((5+len)/6)^α`）
- [ ] 换成 **Pre-LN** 对照实验 —— 观察能否去掉 warmup
- [ ] `evaluate()` 抽样评估 + 修掉 `test()` 与 `os` 两个 bug
- [ ] 导出 attention 热力图，看**交叉注意力对齐**（英文词 ↔ 中文词）——这是可解释性最直观的一次
- [ ] 对比 **Transformer vs LLM API 翻译**：同一批句子，BLEU / 人工评分 / 成本 / 延迟

---

## 12. 一句话收尾

**会调 API 叫"用工具"，能把这套架构从零写出来、训起来、评出来，才叫"懂模型"。**

2600 行的黑盒（`nn.Transformer`）被拆成 330 行看得懂的代码之后，Transformer 从"知识点"变成了"手上的东西"。
