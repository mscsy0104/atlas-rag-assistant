from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_USERNAME = os.getenv("MONGODB_USERNAME")
DB_PASSWORD = os.getenv("MONGODB_PASSWORD")

# OPENAI API
ai_client = OpenAI(api_key=OPENAI_API_KEY)
model = 'text-embedding-3-small'

# MONGODB API
uri = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.tmm4plt.mongodb.net/?appName=Cluster0"
db_client = MongoClient(uri, server_api=ServerApi('1'))

# 데이터베이스 및 컬렉션 설정
db = db_client["ProjectInsightHub"]
collection = db["rag_docs"]

def update_embeddings():
    """
    MongoDB의 rag_docs 컬렉션에서 vector_content_embedding이 없는 문서들을 찾아
    vector_content를 임베딩하여 업데이트합니다.
    """
    # 임베딩이 없는 문서들 찾기
    docs_to_update = list(collection.find({"vector_content_embedding": {"$exists": False}}))
    total_count = len(docs_to_update)
    
    if total_count == 0:
        print("✅ 모든 문서에 임베딩이 이미 존재합니다.")
        return
    
    print(f"📊 임베딩이 필요한 문서: {total_count}개")
    print("🔄 임베딩 생성 및 업데이트 시작...\n")
    
    success_count = 0
    error_count = 0
    
    for idx, doc in enumerate(docs_to_update, 1):
        try:
            # 1. vector_content 읽기
            if 'vector_content' not in doc:
                print(f"⚠️  [{idx}/{total_count}] 문서 ID {doc.get('_id')}: vector_content 필드가 없습니다. 건너뜁니다.")
                error_count += 1
                continue
            
            text_to_embed = doc['vector_content']
            
            if not text_to_embed or not text_to_embed.strip():
                print(f"⚠️  [{idx}/{total_count}] 문서 ID {doc.get('_id')}: vector_content가 비어있습니다. 건너뜁니다.")
                error_count += 1
                continue
            
            # 2. OpenAI Embedding API 호출
            response = ai_client.embeddings.create(
                input=text_to_embed,
                model=model
            )
            embedding = response.data[0].embedding
            
            # 3. MongoDB Document 업데이트 (숫자 배열 저장)
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"vector_content_embedding": embedding}}
            )
            
            success_count += 1
            page_id = doc.get('page_id', 'Unknown')
            print(f"✅ [{idx}/{total_count}] 문서 ID {page_id}: 임베딩 생성 및 업데이트 완료")
            
        except Exception as e:
            error_count += 1
            doc_id = doc.get('_id', 'Unknown')
            print(f"❌ [{idx}/{total_count}] 문서 ID {doc_id}: 오류 발생 - {str(e)}")
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"📊 작업 완료 요약:")
    print(f"   ✅ 성공: {success_count}개")
    print(f"   ❌ 실패: {error_count}개")
    print(f"   📝 전체: {total_count}개")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        # MongoDB 연결 확인
        db_client.admin.command('ping')
        print("✅ MongoDB 연결 성공\n")
        
        # 임베딩 업데이트 실행
        update_embeddings()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
    finally:
        # 연결 종료
        db_client.close()
        print("\n🔌 MongoDB 연결 종료")