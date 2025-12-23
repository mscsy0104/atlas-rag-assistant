"""
RAG 구성을 위한 메타데이터 추출 모듈

Confluence 페이지 JSON에서 RAG 구성에 불필요한 필드를 제거하고
필요한 메타데이터만 추출합니다.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def remove_fields_recursive(data: Any, fields_to_remove: List[str]) -> Any:
    """
    재귀적으로 JSON 구조를 순회하며 지정된 필드들을 제거합니다.
    
    Args:
        data: 제거할 데이터 (dict, list, 또는 기본 타입)
        fields_to_remove: 제거할 필드 이름 리스트
    
    Returns:
        필드가 제거된 데이터
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 제거할 필드인지 확인
            if key in fields_to_remove:
                continue
            
            # 재귀적으로 처리
            result[key] = remove_fields_recursive(value, fields_to_remove)
        
        return result
    
    elif isinstance(data, list):
        return [remove_fields_recursive(item, fields_to_remove) for item in data]
    
    else:
        # 기본 타입 (str, int, float, bool, None)은 그대로 반환
        return data


def extract_metadata_for_rag(json_path: str | Path, output_path: str | Path = None) -> Dict[str, Any]:
    """
    Confluence 페이지 JSON에서 RAG 구성을 위한 메타데이터를 추출합니다.
    
    제거되는 필드:
    - base64EncodedAri
    - profilePicture (모든 위치)
    - _expandable (모든 위치)
    - _links (모든 위치)
    - extensions.position
    - version.minorEdit
    - version.contentTypeModified
    - body.view
    
    Args:
        json_path: 입력 JSON 파일 경로
        output_path: 출력 JSON 파일 경로 (None이면 반환만 함)
    
    Returns:
        메타데이터가 추출된 딕셔너리
    """
    # JSON 파일 로드
    json_path = Path(json_path)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 제거할 필드 리스트 (모든 위치에서 제거)
    fields_to_remove = [
        'base64EncodedAri',
        'profilePicture',
        '_expandable',
        '_links',
        'body'
    ]
    
    # 필드 제거
    cleaned_data = remove_fields_recursive(data, fields_to_remove)
    
    # 특정 경로의 필드들 제거
    # extensions.position
    if 'extensions' in cleaned_data and isinstance(cleaned_data['extensions'], dict):
        cleaned_data['extensions'].pop('position', None)
        # extensions가 비어있으면 제거
        if not cleaned_data['extensions']:
            cleaned_data.pop('extensions', None)
    
    # version.minorEdit, version.contentTypeModified
    if 'version' in cleaned_data and isinstance(cleaned_data['version'], dict):
        cleaned_data['version'].pop('minorEdit', None)
        cleaned_data['version'].pop('contentTypeModified', None)
        cleaned_data['version'].pop('friendlyWhen', None)
        cleaned_data['version'].pop('ncsStepVersion', None)
        cleaned_data['version'].pop('ncsStepVersionSource', None)
        cleaned_data['version'].pop('confRev', None)
    
    # body.view 제거 (body 안의 view 필드만 제거)
    # if 'body' in cleaned_data and isinstance(cleaned_data['body'], dict):
    #     cleaned_data['body'].pop('view', None)
    #     cleaned_data['body'].pop('storage', None)
    
    # 출력 파일로 저장
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print(f"메타데이터 추출 완료: {output_path}")
    
    return cleaned_data


def extract_metadata_batch(input_dir: str | Path, output_dir: str | Path = None, pattern: str = "*.json", recursive: bool = False):
    """
    여러 JSON 파일에 대해 일괄 메타데이터 추출을 수행합니다.
    
    Args:
        input_dir: 입력 디렉토리 경로
        output_dir: 출력 디렉토리 경로 (None이면 입력 디렉토리에 저장)
        pattern: 파일 패턴 (기본값: "*.json")
        recursive: 하위 디렉토리까지 재귀적으로 검색할지 여부 (기본값: False)
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"오류: 입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        return
    
    if not input_dir.is_dir():
        print(f"오류: 입력 경로가 디렉토리가 아닙니다: {input_dir}")
        return
    
    if output_dir is None:
        output_dir = input_dir / "metadata"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 재귀적 검색 여부에 따라 glob 패턴 결정
    if recursive:
        json_files = list(input_dir.rglob(pattern))
    else:
        json_files = list(input_dir.glob(pattern))
    
    if not json_files:
        print(f"경고: {input_dir}에서 {pattern} 패턴의 파일을 찾을 수 없습니다.")
        return
    
    print(f"총 {len(json_files)}개의 파일을 처리합니다...")
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        output_file = output_dir / f"{json_file.stem}_metadata.json"
        try:
            extract_metadata_for_rag(json_file, output_file)
            success_count += 1
        except Exception as e:
            print(f"오류 발생 ({json_file.name}): {e}")
            error_count += 1
    
    print(f"\n처리 완료: 성공 {success_count}개, 실패 {error_count}개")


if __name__ == "__main__":
    # 예시 사용법
    import sys
    
    if len(sys.argv) > 1:
        # --batch 플래그 확인
        if '--batch' in sys.argv:
            batch_idx = sys.argv.index('--batch')
            input_dir = sys.argv[1] if batch_idx > 1 else None
            output_dir = None
            
            # --batch 다음에 출력 디렉토리가 있는지 확인
            if batch_idx + 1 < len(sys.argv) and not sys.argv[batch_idx + 1].startswith('--'):
                output_dir = sys.argv[batch_idx + 1]
            
            # --recursive 플래그 확인
            recursive = '--recursive' in sys.argv or '-r' in sys.argv
            
            if input_dir:
                extract_metadata_batch(input_dir, output_dir, recursive=recursive)
            else:
                print("오류: 배치 모드에서는 입력 디렉토리를 지정해야 합니다.")
                print("사용법: python extract_metadata.py <input_dir> --batch [output_dir] [--recursive]")
        else:
            # 단일 파일 처리 모드
            input_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            
            extract_metadata_for_rag(input_file, output_file)
    else:
        # 기본 예시: page_3400499247.json 처리
        base_dir = Path(__file__).parent.parent
        input_file = base_dir / "fetch" / "data" / "processed" / "page_3400499247.json"
        output_file = base_dir / "fetch" / "data" / "metadata" / "page_3400499247_metadata.json"
        
        if input_file.exists():
            print(f"입력 파일: {input_file}")
            print(f"출력 파일: {output_file}")
            extract_metadata_for_rag(input_file, output_file)
            print("\n추출 완료!")
        else:
            print(f"파일을 찾을 수 없습니다: {input_file}")
            print("\n사용법:")
            print("  단일 파일:")
            print("    python extract_metadata.py <input_json> [output_json]")
            print("  배치 처리:")
            print("    python extract_metadata.py <input_dir> --batch [output_dir] [--recursive]")
            print("\n예시:")
            print("  python extract_metadata.py fetch/data/processed/page_3400499247.json")
            print("  python extract_metadata.py fetch/data/processed --batch fetch/data/metadata")
            print("  python extract_metadata.py fetch/data/processed --batch fetch/data/metadata --recursive")
            print("\n또는 Python 코드에서:")
            print("  from extract_metadata import extract_metadata_for_rag, extract_metadata_batch")
            print("  extract_metadata_for_rag('fetch/data/page_3400499247.json', 'output.json')")
            print("  extract_metadata_batch('fetch/data/processed', 'fetch/data/metadata')")

