#  RAG 还能不用 Embedding？OpenAI 给出了新玩法  
GauravShrivastav  AgenticAI   2025-08-10 10:59  
  
如果你在用LLM构建应用，你很可能已经和RAG打过交道。RAG 对于用外部数据来增强LLM的能力很棒，但其中的检索——往往很复杂。我自己就曾花上好几个小时纠结：切分块的大小、重叠的策略、该用哪种向量嵌入模型。至于管理向量数据库？那更是一个完整的基础设施挑战。  
  
所以，当我在 OpenAI 的 Cookbook 中偶然看到他们关于另一种 RAG 思路的最新研究时——一种号称可以绕过传统嵌入的方案——我的开发者大脑小小地“翻了个跟头”。 难道我们真的可以在没有向量数据库折腾的情况下也获得很好的检索效果？这个想法真有点打破固有模式的意味。  
  
关键秘诀似乎是利用新一代模型（如 GPT-4.1 和 Gemini Flash）超大的上下文窗口。 能一次处理百万 tokens 的模型，让全新的工作流成为可能。不过，难道上下文窗口的大小是唯一的关键因素吗？  
## 1. 超越标准 RAG 流程  
  
传统 RAG 的流程很直接：  
1. **摄取（Ingest）**  
：拆分文档、对每个切块做嵌入、存入向量数据库。  
  
1. **查询（Query）**  
：对查询做嵌入，在数据库中查找相似的切块。  
  
1. **增强并生成（Augment & Generate）**  
：将切块 + 查询一起输入 LLM 生成答案。  
  
这种方式需要大量预处理，并要维护向量索引。它确实稳健，但带来延迟、存储开销，并且强依赖嵌入的质量。 更重要的是，切块的过程可能造成上下文丢失——相关信息被拆到不同块中，检索时被漏掉。  
## 2. Agentic 方法：模仿人类大脑  
  
OpenAI 的 **Agentic RAG**  
 不一样。它是一个多步骤的流程，模拟了你阅读长文档找答案的方式。你不会逐字阅读，而是会先快速浏览，找到可能有用的部分，再深入阅读，并提取关键信息。这种方法在每个阶段调用不同的 LLM，就像一组分工明确的“智能代理”在协作。 这引发了一个有趣的问题：这种方法真的是“没有嵌入”吗？还是说 LLM 在注意力机制中，隐式地创建并使用了一种“语义表示”？  
## 3. 一个多步骤的流程  
### 3.1. 加载文档  
```
import requests# ... other imports ...def load_document(url: str) -> str:    """Load a document from a URL and return its text content."""    print(f"Downloading document from {url}...")    response = requests.get(url)    response.raise_for_status()    # ... (pdf reading and text extraction) ...    return full_text# Load the document (e.g., a legal manual with 900k+ tokens)document_text = load_document("https://www.uspto.gov/sites/default/files/documents/tbmp-Master-June2024.pdf")
```  
### 3.2. 分割  
```
# ... (tokenizer import) ...def split_into_20_chunks(text: str, min_tokens: int = 500) -> List[Dict[str, Any]]:    """Split text into up to 20 chunks, respecting sentence boundaries."""    sentences = sent_tokenize(text)    tokenizer = tiktoken.get_encoding(TOKENIZER_NAME)    # ... (logic to build chunks from sentences and handle chunk size) ...    return chunksdocument_chunks = split_into_20_chunks(document_text, min_tokens=500)# This results in ~20 chunks, each potentially holding tens of thousands of tokens.
```  
### 3.3. 路由  
```
# ... (OpenAI client setup) ...def route_chunks(question: str, chunks: List[Dict[str, Any]],                depth: int, scratchpad: str = "") -> Dict[str, Any]:    """Ask the model which chunks contain info relevant to the question."""    # ... (system prompt defining role as document navigator) ...    user_message = f"QUESTION: {question}\n\n"    if scratchpad:        user_message += f"CURRENT SCRATCHPAD:\n{scratchpad}\n\n"    user_message += "TEXT CHUNKS:\n\n"    # ... (add chunks text with IDs to user_message) ...    # Step 1: Ask model to record reasoning in scratchpad (required tool call)    # ... (model call with tools and tool_choice="required") ...    # ... (process tool call, update scratchpad) ...    # Step 2: Ask model to select relevant chunk IDs (structured output)    text_format = { "format": { "type": "json_schema", "name": "selected_chunks", ... } }    # ... (model call with text_format) ...    # ... (extract selected_ids from JSON response) ...    return { "selected_ids": selected_ids, "scratchpad": new_scratchpad }
```  
  
然后，navigate_to_paragraphs  
 函数会递归调用 route_chunks  
，沿着文档的层级结构逐步向下钻取，直到内容被细化到足够精细的粒度为止。  
### 3.4. 生成答案  
```
from pydantic import BaseModel, field_validatorfrom typing import List, Literalclass LegalAnswer(BaseModel):    answer: str    citations: List[str]@field_validator('citations')def validate_citations(cls, citations, info):        # ... (logic to check if citations match passed valid IDs) ...        return citationsdef generate_answer(question: str, paragraphs: List[Dict[str, Any]],                   scratchpad: str) -> LegalAnswer:    """Generate an answer from the retrieved paragraphs."""    # ... (prepare context string from paragraphs with IDs) ...    # ... (system prompt focusing on answering ONLY from provided text) ...        response = client.responses.parse(        model="gpt-4.1",        input=[            {"role": "system", "content": system_prompt.format(...)},            {"role": "user", "content": f"QUESTION: {question}\n\nSCRATCHPAD: {scratchpad}\n\nPARAGRAPHS:\n{context}"}        ],        text_format=LegalAnswer,        temperature=0.3    )    return response.output_parsed
```  
  
结合 Pydantic 的结构化输出与 field_validator  
，可以确保引用格式有效，并提升可追溯性。  
### 3.5. 答案验证  
```
class VerificationResult(BaseModel):    is_accurate: bool    explanation: str    confidence: Literal["high", "medium", "low"]def verify_answer(question: str, answer: LegalAnswer,                   cited_paragraphs: List[Dict[str, Any]]) -> VerificationResult:    """Verify if the answer is grounded in the cited paragraphs."""    # ... (prepare context string from cited paragraphs with IDs) ...    system_prompt = """You are a fact-checker for legal information.Your job is to verify if the provided answer:1. Is factually accurate according to the source paragraphs2. Uses citations correctly# ... (instructions for confidence scoring) ..."""    response = client.responses.parse(        model="o4-mini",        input=[            {"role": "system", "content": system_prompt},            {"role": "user", "content": f"QUESTION: {question}\n\nANSWER TO VERIFY:\n{answer.answer}\n\nCITATIONS USED: {', '.join(answer.citations)}\n\nSOURCE PARAGRAPHS:\n{context}"}        ],        text_format=VerificationResult    )    return response.output_parsed
```  
  
这个 **LLM 充当裁判（LLM-as-Judge）**  
 的步骤，相当于关键的最终审核环节，能够提升整个系统的整体可靠性。  
## 4. 深入 OpenAI 的 Agentic 策略  
  
虽然 OpenAI 推出的 **Agentic 检索**  
 在理念上确实很前沿，但在全盘接受之前，我们有必要先踩一脚刹车，仔细看看它可能会在哪些地方出错，以及与传统的 RAG 相比，它的优劣在哪里。  
### 4.1 成本与等待时间  
  
第一个明显的感受？**成本高、延迟大**  
。 和快速直查向量数据库不同，这种方法在每次查询时需要多次调用 LLM。计算消耗和等待时间都会显著增加。 那么问题来了：当数据量膨胀、问题复杂化时，这种金钱与时间的负担会如何扩散？ 能否通过一些优化降低开销？比如缓存中间步骤、或者用更小、更快的模型处理最初的路由调用，这可能是聪明的做法。  
### 4.2 扩展的痛点  
  
处理一份文档时，这套方法感觉还不错。 但如果要跨**成千上万份**  
文档检索？那就是另一场比赛了。在这个规模下，文档级的预筛选或索引已非可选，而是必需。 更可行的路线可能是**混合模式**  
：先用快速、粗粒度的方法锁定候选文档，再让 Agentic 系统对选中的少数进行深度推理。  
### 4.3 无法避免的上下文限制  
  
即使是最新模型，拥有**百万 token**  
 级的上下文窗口（惊艳！），它们也终究有极限。对于特别庞大或结构极其复杂的文档，这种 Agentic 系统仍可能力不从心。问题是：它能多好地处理超出上下文容量的文档？未来版本也许可以用**迭代式摘要**  
或**智能上下文压缩**  
来解决这个障碍。  
### 4.4 查询并不平等  
  
并非所有问题的难度都一样。简单的事实类问题？速度可能很快。但多部分、抽象类问题呢？显然更棘手。 系统中的“草稿板”机制，能否为复杂推理提供足够支持？还是需要额外的工具和推理辅助机制？  
### 4.5 系统幻觉  
  
任何基于 LLM 的系统都存在“胡编乱造”的风险。Agentic 流程中增加了多步验证机制，正是为了对抗这种幻觉。但它是否真的坚不可摧？会不会在某些微妙的错误场景下被漏检？如果能做一份传统 RAG 与 Agentic 方法的**幻觉率对比实验**  
，应该会很有价值。  
### 4.6 Embedding 消失了，还是被整合了？  
  
最后，一个更哲学化的问题：这真的是**“无嵌入”**吗？ 在注意力机制内部，LLM 确实会构建输入的内部语义表示——这本身就是一种动态嵌入。所以，与其说它废弃了嵌入，不如说它是**  
把 Embedding 直接融入了检索与推理的核心回路中**，改变了它们的使用方式。  
## 5. 优劣权衡  
  
这种 **Agentic 风格的 RAG**  
 虽然聪明且富有创意，但它同样伴随着一系列取舍。**优势方面**  
，它带来了令人惊喜的 **零摄取延迟**  
——也就是说，你可以立即查询全新的文档，无需等待冗长的预处理过程。它在文档中穿行的方式很优雅，有点像人类的阅读习惯：需要时深入挖掘。这种动态的分层式导航，往往能在复杂问题中找到更精准的答案，尤其是在跨章节、跨部分进行关联推理时。此外，在核心检索部分，你完全跳过了繁琐的索引基础设施，这让部署变得简单得多。最关键的是，当**准确性**  
至关重要时，那种显式、结构化的验证过程会增加额外的信任保障，确保答案确实得到了来源的支持。  
  
**劣势方面**  
，这些好处并非免费。这种方法在每个查询中要多次调用 LLM，而不是一次快速、廉价的向量数据库查找，因此每次查询的成本自然更高。延迟方面，由于递归式的文档探索，你也会感觉响应时间变长。 此外，这种无索引的实现方式在**可扩展性**  
上不如传统 RAG——当面对真正海量的文档时，除非事先增加某种预筛选，否则会显得有些吃力。  
## 6. 何时该用它  
  
综合这些优缺点，这种方法最适合应对**长篇、专业性强的文档**  
中的复杂问题——比如详尽的法律意见书或密集的技术手册——在这些场景下，信息的**绝对准确**  
以及**精确引用**  
是不可妥协的要求。 它同样适合**数据持续变动**  
的环境，因为你无需不停地重建静态索引。 反之，如果你的目标是一个**超快响应**  
、需要从**庞大的静态数据集**  
中迅速提取信息的通用型聊天机器人，传统基于嵌入的 RAG 可能依旧是你的最佳选择。  
## 7. 探索未来思路  
  
OpenAI 自然也在思考这种方法的进化方向。 一个想法是 **混合系统**  
：先用传统嵌入检索快速缩小范围，再让 Agentic 系统在这个更小、更可控的集合中进行推理。 另一个很酷的可能性是：利用超大的上下文窗口，在文档层面**一次性构建详细的知识图谱**  
作为前置任务，然后用另一个可能更轻量的模型，在该图谱中快速查询——相当于结合两种方案的优势。 最后是**粒度可调**  
：让用户指定系统深入的程度——需要句子级别的证据（在法律工作中很关键），还是段落级别的引用（在新闻分析中可能已经足够）。 关键在于在**精确度**  
与**运营成本**  
之间找到那个最佳平衡点。  
## 总结  
  
深入研究这种 Agentic RAG 方法，让我确认了几个核心要点：  
- **百万 token 级上下文窗口**  
 是一个重大突破，让即席的、流畅的文档探索成为可能；  
  
- 它的分层阅读方式贴近自然习惯，有助于在复杂问题中锁定相关信息；  
  
- “草稿板”机制提升了推理能力，让模型能逐步拆解问题；  
  
- 无需数据库搭建就能快速上手（至少在核心检索部分）是一个实用优势；  
  
- 最重要的是，内置的验证步骤让人更信任答案，因为它们确实直接来自并经过来源验证。  
  
总体而言，这种 Agentic RAG 的确令人兴奋。它很好地展示了大型语言模型——尤其是拥有大上下文窗口和代理能力的 LLM——如何以全新且强大的方式解决复杂的信息问题，特别是在**准确性**  
与**深入理解**  
比**速度**  
或**批量处理能力**  
更重要的场景中。  
  
最后，分享可实操的Colab全文代码：https://colab.research.google.com/drive/15FuQByD4hVFpqw3Isc_nqVba1Zp_o4Ie?usp=sharing  
> 本文分享自Medium好文《RAG Without Embeddings? Here's how OpenAI is doing this…》，作者：Gaurav Shrivastav，可以原文访问。  
  
  
