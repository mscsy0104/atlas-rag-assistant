import json
from pathlib import Path
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

final_rag_data_dir = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/final_rag_data')

# MongoDB 연결 설정
DB_USERNAME = os.getenv("MONGODB_USERNAME")
DB_PASSWORD = os.getenv("MONGODB_PASSWORD")
uri = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.tmm4plt.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

# 데이터베이스 및 컬렉션 설정
db = client["ProjectInsightHub"]
collection = db["rag_docs"]

def load_jsonl(file_path: Path) -> dict:
    """JSONL 파일을 읽어서 page_id/id를 키로 하는 딕셔너리로 변환"""
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                # page_id 또는 id를 키로 사용
                key = obj.get('page_id') or obj.get('id')
                if key:
                    data[key] = obj
    return data

def merge_data():
    """5개의 JSONL 파일을 page_id/id로 연결하여 최종 데이터 생성"""
    
    # 각 파일 로드
    print("JSONL 파일들을 로드하는 중...")
    html_body_toc = load_jsonl(final_rag_data_dir / 'html_body_toc.jsonl')
    merged_llm_resps = load_jsonl(final_rag_data_dir / 'merged_llm_resps.jsonl')
    merged_metadata = load_jsonl(final_rag_data_dir / 'merged_metadata.jsonl')
    merged_tables = load_jsonl(final_rag_data_dir / 'merged_tables.jsonl')
    vector_contents = load_jsonl(final_rag_data_dir / 'vector_contents.jsonl')
    
    # 모든 page_id 수집 (어느 파일에서든)
    all_page_ids = set()
    all_page_ids.update(html_body_toc.keys())
    all_page_ids.update(merged_llm_resps.keys())
    all_page_ids.update(merged_metadata.keys())
    all_page_ids.update(merged_tables.keys())
    all_page_ids.update(vector_contents.keys())
    
    print(f"총 {len(all_page_ids)}개의 페이지 ID를 찾았습니다.")
    
    # 각 page_id에 대해 데이터 병합
    final_documents = []
    for page_id in all_page_ids:
        doc = {
            'page_id': page_id
        }
        
        # html_body_toc 데이터 병합
        if page_id in html_body_toc:
            doc['toc'] = html_body_toc[page_id].get('toc')
        
        # merged_llm_resps 데이터 병합
        if page_id in merged_llm_resps:
            llm_data = merged_llm_resps[page_id].get('content', {})
            doc['llm_content'] = llm_data
        
        # merged_metadata 데이터 병합 (id 필드 사용)
        if page_id in merged_metadata:
            metadata = merged_metadata[page_id].copy()
            # id 필드를 page_id로 통일 (이미 page_id가 있으므로 중복 제거)
            if 'id' in metadata:
                metadata.pop('id', None)
            doc['metadata'] = metadata
        
        # merged_tables 데이터 병합
        if page_id in merged_tables:
            doc['tables'] = merged_tables[page_id].get('tables')
        
        # vector_contents 데이터 병합
        if page_id in vector_contents:
            vector_data = vector_contents[page_id]
            doc['vector_content'] = vector_data.get('vector_content')
            # vector_contents의 metadata도 병합 (기존 metadata와 병합)
            if 'metadata' in vector_data:
                if 'metadata' not in doc:
                    doc['metadata'] = {}
                doc['metadata'].update(vector_data['metadata'])
        
        final_documents.append(doc)
    
    return final_documents

def insert_to_mongodb(documents):
    """MongoDB에 문서 삽입"""
    print(f"\nMongoDB에 {len(documents)}개의 문서를 삽입하는 중...")
    
    # 기존 데이터 삭제 (선택사항 - 필요시 주석 해제)
    # collection.delete_many({})
    
    # 배치로 삽입
    try:
        result = collection.insert_many(documents)
        print(f"✅ 성공적으로 {len(result.inserted_ids)}개의 문서를 삽입했습니다.")
    except Exception as batch_error:
        print(f"❌ 배치 삽입 오류 발생: {batch_error}")
        # 개별 삽입으로 재시도
        print("개별 삽입으로 재시도 중...")
        success_count = 0
        for doc in documents:
            try:
                collection.insert_one(doc)
                success_count += 1
            except Exception as insert_error:
                print(f"문서 {doc.get('page_id')} 삽입 실패: {insert_error}")
        print(f"✅ {success_count}/{len(documents)}개의 문서를 삽입했습니다.")

def main():
    print("=" * 80)
    print("RAG 객체 생성 및 MongoDB 삽입 시작")
    print("=" * 80)
    
    # 데이터 병합
    final_documents = merge_data()
    
    print(f"\n병합된 문서 수: {len(final_documents)}")
    
    # 샘플 출력 (첫 번째 문서)
    if final_documents:
        print("\n첫 번째 문서 샘플:")
        print(json.dumps(final_documents[0], ensure_ascii=False, indent=2))
    
    # MongoDB에 삽입
    insert_to_mongodb(final_documents)
    
    # 연결 종료
    client.close()
    print("\n작업 완료!")

if __name__ == "__main__":
    main()
