import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
import traceback

# --- Custom Exceptions ---
class MetadataExtractionError(Exception): pass
class InvalidJSONFormatError(MetadataExtractionError): pass
class SchemaValidationError(MetadataExtractionError): pass

# --- Business Logic ---
def remove_fields_recursive(data: Any, fields_to_remove: List[str]) -> Any:
    """재귀적으로 필드를 제거 (Pythonic한 딕셔너리 컴프리헨션 활용)"""
    if isinstance(data, dict):
        return {
            k: remove_fields_recursive(v, fields_to_remove)
            for k, v in data.items() if k not in fields_to_remove
        }
    elif isinstance(data, list):
        return [remove_fields_recursive(item, fields_to_remove) for item in data]
    return data

def extract_metadata(json_path: Path, output_path: Path = None) -> Dict[str, Any]:
    """
    내부 검증: 파일 읽기 권한, JSON 형식 준수 여부 등을 확인
    """
    try:
        # EAFP: 일단 열어보고 문제 있으면 예외로 처리
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidJSONFormatError(f"JSON 파싱 실패 ({json_path.name}): {e}") from e
    except PermissionError as exc:
        raise MetadataExtractionError(f"파일 읽기 권한이 없습니다: {json_path}") from exc

    # 비즈니스 검증: 최소한의 데이터 구조 확인
    if not isinstance(data, dict):
        raise SchemaValidationError(f"예상치 못한 데이터 구조입니다 (Expected dict, got {type(data).__name__})")

    fields_to_remove = ['base64EncodedAri', 'macroRenderedOutput', 'body', 'extensions', '_expandable', '_links']
    cleaned_data = remove_fields_recursive(data, fields_to_remove)
    
    # 특정 깊은 경로 필드 정제 (Safe Access 사용)
    if 'history' in cleaned_data:
        if 'latest' in cleaned_data['history'] and isinstance(cleaned_data['history']['latest'], bool):
            cleaned_data['history'].pop('latest', None)
        if 'createdBy' in cleaned_data['history'] and isinstance(cleaned_data['history']['createdBy'], dict):
            for field in ['type', 'accountType', 'email', 'publicName', 'profilePicture', 'isExternalCollaborator', 'isGuest', 'locale', 'accountStatus', '_expandable', '_links']:
                cleaned_data['history']['createdBy'].pop(field, None)

    if 'version' in cleaned_data and isinstance(cleaned_data['version'], dict):
        for field in ['contentTypeModified', 'friendlyWhen', 'message', 'minorEdit', 'ncsStepVersion', 'ncsStepVersionSource', 'confRev', '_expandable', '_links']:
            cleaned_data['version'].pop(field, None)
        if 'by' in cleaned_data['version'] and isinstance(cleaned_data['version']['by'], dict):
            for field in ['type', 'accountType', 'email', 'publicName', 'profilePicture', 'isExternalCollaborator', 'isGuest', 'locale', 'accountStatus', '_expandable', '_links']:
                cleaned_data['version']['by'].pop(field, None)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    return cleaned_data

def batch_extract_metadata(input_dir: Path, output_dir: Path):
    """배치 처리 시 개별 파일의 에러가 전체 공정을 멈추지 않도록 관리"""
    # 밖에서 체크: 입력 디렉토리가 존재하는가?
    if not input_dir.is_dir():
        raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    json_files = list(input_dir.rglob('*.json'))
    
    print(f"🚀 처리 시작: {len(json_files)}개의 파일 발견")
    
    for json_file in json_files:
        print(f"🔍 처리 중: {json_file.name}")
    
    results = {"success": 0, "failure": 0}
    for json_file in json_files:
        try:
            output_file = output_dir / f"{json_file.stem}_metadata.json"
            extract_metadata(json_file, output_file)
            results["success"] += 1
        except MetadataExtractionError as e:
            # 커스텀 예외를 잡아 상세히 보고하지만, 루프는 계속됨
            print(f"❌ 실패 ({json_file.name}): {e}")
            results["failure"] += 1
            
    print(f"\n✅ 완료: 성공 {results['success']}, 실패 {results['failure']}")

# --- Entry Point ---
def main():
    parser = argparse.ArgumentParser(description='Confluence RAG Metadata Extractor')
    parser.add_argument('input', nargs='?', help='입력 경로')
    parser.add_argument('output', nargs='?', help='출력 경로')
    parser.add_argument('--batch', action='store_true', help='배치 처리 모드')
    args = parser.parse_args()

    # 경로 설정 (Pathlib 활용)
    base_input = Path(args.input) if args.input else Path("/Users/sychoi/ProjectInsightHub/data/fetched/json")
    base_output = Path(args.output) if args.output else Path("/Users/sychoi/ProjectInsightHub/data/processed/metadata")

    try:
        # 입력 경로가 디렉토리인지 확인
        if base_input.is_dir() or args.batch:
            # 디렉토리면 자동으로 배치 모드로 처리
            batch_extract_metadata(base_input, base_output)
        else:
            # 단일 파일 처리 시에도 존재 여부 우선 체크 (Main의 책임)
            if not base_input.exists():
                print(f"Critical: 입력 파일이 존재하지 않습니다: {base_input}")
                sys.exit(1)
            if base_input.is_dir():
                print(f"Critical: 입력 경로가 디렉토리입니다. 파일을 지정하거나 --batch 플래그를 사용하세요: {base_input}")
                sys.exit(1)
            extract_metadata(base_input, base_output)
            print(f"✨ 단일 파일 처리 완료: {base_input.name}")
            
    except Exception as e:
        # 모든 예외에 대한 최종 방어선
        print(f"에러 발생: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()