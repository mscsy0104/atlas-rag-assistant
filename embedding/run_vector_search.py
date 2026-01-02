from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# 1. 초기화 (API 키 및 DB 연결)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_USERNAME = os.getenv("MONGODB_USERNAME")
DB_PASSWORD = os.getenv("MONGODB_PASSWORD")

ai_client = OpenAI(api_key=OPENAI_API_KEY)
model = 'text-embedding-3-small'

uri = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.tmm4plt.mongodb.net/?appName=Cluster0"
db_client = MongoClient(uri, server_api=ServerApi('1'))
db = db_client["ProjectInsightHub"]
collection = db["rag_docs"]

def ask_rag_system(user_query):
    # 2. 질문 임베딩 (적재할 때와 동일한 모델 사용)
    query_vector = ai_client.embeddings.create(
        input=user_query,
        model=model
    ).data[0].embedding

    # 3. MongoDB Vector Search 수행
    pipeline = [
        {
            "$vectorSearch": {
                "index": "default", # 생성한 인덱스 이름 (보통 default)
                "path": "vector_content_embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": 3  # 가장 유사한 상위 3개 문서 추출
            }
        },
        {
            "$project": {
                "_id": 0,
                "metadata.title": 1,
                "toc": 1,
                "llm_content": 1,
                "tables": 1,
                "vector_content": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]

    results = list(collection.aggregate(pipeline))
    return results

# 4. 실제 질문 던져보기
# 적절한 질문 예시들 (문서에 실제로 답이 있을 가능성이 높은 질문들)
sample_queries = [
]

def print_search_results(query, search_results):
    """검색 결과를 보기 좋게 출력"""
    print(f"\n{'='*70}")
    print(f"🔍 질문: {query}")
    print(f"{'='*70}")
    
    if not search_results:
        print("❌ 검색 결과가 없습니다.")
        return
    
    print(f"✅ 검색 결과: {len(search_results)}개 문서 발견\n")
    for i, doc in enumerate(search_results, 1):
        title = doc.get('metadata', {}).get('title', '제목 없음')
        score = doc.get('score', 0)
        print(f"[{i}] {title}")
        print(f"    유사도 점수: {score:.4f}")
        
        # llm_content가 있는 경우 요약 출력
        llm_content = doc.get('llm_content', {})
        if isinstance(llm_content, dict) and 'summary' in llm_content:
            summary = llm_content['summary']
            if summary:
                print(f"    📄 내용 요약: {summary[:200]}...")
        
        # toc가 있는 경우 구조 출력
        toc = doc.get('toc', '')
        if toc and len(toc) > 0:
            toc_preview = toc[:150] + "..." if len(toc) > 150 else toc
            print(f"    📑 문서 구조: {toc_preview}")
        
        print()

# # 첫 번째 질문으로 테스트
# test_query = sample_queries[0]
# test_results = ask_rag_system(test_query)
# print_search_results(test_query, test_results)

# # 결과가 없으면 다른 질문들도 시도
# if not test_results:
#     print("\n💡 다른 추천 질문들:")
#     for idx, q in enumerate(sample_queries[1:], 1):
#         print(f"   {idx}. {q}")
    
#     # 두 번째 질문도 자동으로 시도
#     if len(sample_queries) > 1:
#         print(f"\n🔄 다음 질문으로 자동 시도: {sample_queries[1]}")
#         test_results_2 = ask_rag_system(sample_queries[1])
#         print_search_results(sample_queries[1], test_results_2)

# 첫 번째 질문으로 테스트
for test_query in sample_queries:
    test_results = ask_rag_system(test_query)
    print_search_results(test_query, test_results)