from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Any
import uvicorn
from pathlib import Path

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

app = FastAPI()

# 데이터베이스 파일의 절대 경로 설정 (Windows 예시)
db_directory = Path("C:/Python").resolve()
db_directory.mkdir(parents=True, exist_ok=True)  # 디렉토리 없으면 생성
db_path = db_directory / "saved_data.db"

# SQLAlchemy용 SQLite URL 생성
DATABASE_URL = f"sqlite:///{db_path}"

# SQLite 데이터베이스 설정
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite는 기본적으로 스레드 안전하지 않음
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 모델 정의
class SavedData(Base):
    __tablename__ = "saved_data"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    rows = relationship("DataRow", back_populates="saved_data", cascade="all, delete-orphan")

class DataRow(Base):
    __tablename__ = "data_row"
    id = Column(Integer, primary_key=True, index=True)
    saved_data_id = Column(Integer, ForeignKey("saved_data.id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    
    saved_data = relationship("SavedData", back_populates="rows")
    cells = relationship("DataCell", back_populates="data_row", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint('saved_data_id', 'row_number', name='_saveddata_row_uc'),)

class DataCell(Base):
    __tablename__ = "data_cell"
    id = Column(Integer, primary_key=True, index=True)
    data_row_id = Column(Integer, ForeignKey("data_row.id"), nullable=False)
    column_name = Column(String, nullable=False)
    value = Column(String, nullable=True)
    
    data_row = relationship("DataRow", back_populates="cells")
    
    __table_args__ = (UniqueConstraint('data_row_id', 'column_name', name='_datarow_column_uc'),)

# 데이터베이스 생성
Base.metadata.create_all(bind=engine)

# 종속성: 데이터베이스 세션 제공
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CORS 설정 (필요 시)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 형식을 지정하는 Pydantic 모델
class DataModel(BaseModel):
    headers: List[str]
    data: List[List[Any]]

# HTML로 웹 페이지 제공
@app.get("/", response_class=HTMLResponse)
async def get_excel_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Excel-like DB Saver</title>
        <script src="https://cdn.jsdelivr.net/npm/handsontable@8.0.0/dist/handsontable.full.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/handsontable@8.0.0/dist/handsontable.full.min.css" rel="stylesheet">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            #header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            #buttonGroup {
                display: flex;
                align-items: center;
            }
            #buttonGroup button, #buttonGroup select, #buttonGroup input[type="text"] {
                margin-left: 10px;
                padding: 5px 10px;
                font-size: 14px;
            }
            #controls {
                margin-bottom: 10px;
            }
            #controls button {
                margin-right: 10px;
                padding: 5px 10px;
                font-size: 14px;
            }
            #excel {
                width: 100%;
                height: 400px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h3>웹 Excel 형태 - DB 저장 및 불러오기</h3>
            <div id="buttonGroup">
                <input type="text" id="filenameInput" placeholder="파일 이름 입력 (선택)">
                <button onclick="saveData()">저장</button>
                <select id="jsonFiles">
                    <option value="">-- 파일 선택 --</option>
                </select>
                <button onclick="loadData()">불러오기</button>
            </div>
        </div>
        
        <div id="controls">
            <button onclick="addRow()">행 추가</button>
            <button onclick="addColumn()">열 추가</button>
        </div>
        
        <div id="excel"></div>
        <script>
            const container = document.getElementById('excel');
            let hot = new Handsontable(container, {
                data: Handsontable.helper.createSpreadsheetData(5, 3),  // 초기 행과 열을 최소화
                rowHeaders: true,
                colHeaders: true,  // 기본 열 헤더 사용
                licenseKey: 'non-commercial-and-evaluation',
                contextMenu: true,  // 컨텍스트 메뉴 활성화
                minRows: 1,
                minCols: 1,
                manualColumnResize: true,
                manualRowResize: true,
                columnSorting: true,
                // 열 헤더를 직접 편집할 수 있도록 설정
                afterGetColHeader: function(col, TH) {
                    // 열 헤더를 더블 클릭하면 편집 모드로 전환
                    TH.style.cursor = 'pointer';
                    TH.addEventListener('dblclick', function() {
                        const newName = prompt("새 열 이름을 입력하세요:", hot.getColHeader(col));
                        if (newName !== null && newName.trim() !== "") {
                            hot.setColHeader(col, newName.trim());
                        }
                    });
                }
            });

            // 페이지 로드 시 JSON 파일 목록 가져오기
            window.onload = async function() {
                await fetchJsonFileList();
            };

            async function fetchJsonFileList() {
                try {
                    const response = await fetch("/list_json");
                    const files = await response.json();
                    const select = document.getElementById('jsonFiles');
                    // 기존 옵션 제거 (초기 옵션만 남김)
                    select.innerHTML = '<option value="">-- 파일 선택 --</option>';
                    files.forEach(file => {
                        const option = document.createElement('option');
                        option.value = file;
                        option.text = file;
                        select.appendChild(option);
                    });
                } catch (error) {
                    console.error("JSON 파일 목록을 가져오는 데 실패했습니다:", error);
                }
            }
            
            async function saveData() {
                const colCount = hot.countCols();
                const headers = [];
                for (let i = 0; i < colCount; i++) {
                    headers.push(hot.getColHeader(i));
                }
                const data = hot.getData();

                const payload = { headers, data };
                const filenameInput = document.getElementById("filenameInput").value.trim();
                const url = filenameInput ? `/save?filename=${encodeURIComponent(filenameInput)}` : "/save";
                try {
                    const response = await fetch(url, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    const result = await response.json();
                    if (result.link) {
                        alert(`저장되었습니다: ${window.location.origin}${result.link}`);
                        
                        // 새 파일을 드롭다운에 추가
                        const select = document.getElementById('jsonFiles');
                        const filename = result.link.split('/').pop();
                        const option = document.createElement('option');
                        option.value = filename;
                        option.text = filename;
                        select.appendChild(option);
                    } else {
                        alert("저장에 실패했습니다. 다시 시도해 주세요.");
                    }
                } catch (error) {
                    console.error("데이터 저장 중 오류 발생:", error);
                    alert("저장에 실패했습니다. 다시 시도해 주세요.");
                }
            }

            async function loadData() {
                const select = document.getElementById('jsonFiles');
                const filename = select.value;
                if (!filename) {
                    alert("불러올 파일을 선택해주세요.");
                    return;
                }
                try {
                    const response = await fetch(`/data/${filename}`);
                    if (response.ok) {
                        const result = await response.json();
                        const headers = result.headers;
                        const data = result.data.map(row => headers.map(header => row[header]));
                        setHeaders(headers);
                        hot.loadData(data);
                        alert("데이터를 성공적으로 불러왔습니다.");
                    } else {
                        alert("파일을 불러오는 데 실패했습니다.");
                    }
                } catch (error) {
                    console.error("데이터 불러오는 중 오류 발생:", error);
                    alert("파일을 불러오는 데 실패했습니다.");
                }
            }

            function addRow() {
                hot.alter('insert_row');
            }
            function addColumn() {
                const currentColCount = hot.countCols();
                hot.alter('insert_col');
                // Handsontable의 colHeaders를 업데이트 (자동으로 생성)
                hot.updateSettings({
                    colHeaders: hot.getColHeader()
                });
            }

            function setHeaders(headers) {
                // Handsontable의 열 헤더를 설정
                hot.updateSettings({
                    colHeaders: headers
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)      

# 데이터베이스에 데이터 저장 엔드포인트
@app.post("/save")
async def save_data(
    data_model: DataModel,
    filename: str = Query(None),
    db: Session = Depends(get_db)
):
    # 파일 이름이 지정되지 않은 경우 기본 파일 이름 생성
    if not filename:
        filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        # 파일 이름에 .json 확장자가 없으면 추가
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
    
    # SavedData 엔트리 가져오기 또는 새로 생성
    saved_data = db.query(SavedData).filter(SavedData.name == filename).first()
    if not saved_data:
        saved_data = SavedData(name=filename)
        db.add(saved_data)
        db.commit()
        db.refresh(saved_data)
    
    # 기존 행 삭제 (업데이트 용도)
    db.query(DataRow).filter(DataRow.saved_data_id == saved_data.id).delete()
    db.commit()
    
    # headers와 data를 데이터베이스에 저장
    for row_idx, row in enumerate(data_model.data, start=1):
        data_row = DataRow(saved_data_id=saved_data.id, row_number=row_idx)
        db.add(data_row)
        db.commit()
        db.refresh(data_row)
        
        for col_idx, cell in enumerate(row):
            if col_idx < len(data_model.headers):
                column_name = data_model.headers[col_idx]
            else:
                column_name = f"Column{col_idx + 1}"
            
            data_cell = DataCell(
                data_row_id=data_row.id,
                column_name=column_name,
                value=str(cell) if cell is not None else ""
            )
            db.add(data_cell)
        db.commit()
    
    # 저장된 파일 링크 생성
    file_link = f"/data/{filename}"
    return JSONResponse(content={"link": file_link})

# 특정 파일의 데이터 조회 엔드포인트
@app.get("/data/{filename}", response_class=JSONResponse)
async def get_data_detail(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    특정 파일 이름에 해당하는 데이터 세트를 조회합니다.
    """
    saved_data = db.query(SavedData).filter(SavedData.name == filename).first()
    if not saved_data:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    # 모든 행과 셀을 조회
    rows = db.query(DataRow).filter(DataRow.saved_data_id == saved_data.id).order_by(DataRow.row_number).all()
    
    headers_set = set()
    data = []
    for row in rows:
        row_data = {}
        for cell in row.cells:
            row_data[cell.column_name] = cell.value
            headers_set.add(cell.column_name)
        data.append(row_data)
    
    headers = sorted(list(headers_set))  # 일관된 순서를 위해 정렬
    return {"headers": headers, "data": data}

# JSON 파일 목록 제공 엔드포인트
@app.get("/list_json", response_class=JSONResponse)
async def list_json_files(db: Session = Depends(get_db)):
    files = db.query(SavedData.name).all()
    file_list = [file[0] for file in files]
    return file_list

# 전체 데이터 목록 조회 엔드포인트 추가
@app.get("/all_data", response_class=JSONResponse)
async def get_all_data(db: Session = Depends(get_db)):
    """
    데이터베이스에 저장된 모든 데이터 세트를 조회합니다.
    """
    saved_data_entries = db.query(SavedData).all()
    result = []
    for entry in saved_data_entries:
        # 각 데이터 세트의 헤더와 데이터를 가져오기
        rows = db.query(DataRow).filter(DataRow.saved_data_id == entry.id).order_by(DataRow.row_number).all()
        
        headers_set = set()
        data = []
        for row in rows:
            row_data = {}
            for cell in row.cells:
                row_data[cell.column_name] = cell.value
                headers_set.add(cell.column_name)
            data.append(row_data)
        
        headers = sorted(list(headers_set))  # 일관된 순서를 위해 정렬
        
        result.append({
            "id": entry.id,
            "name": entry.name,
            "headers": headers,
            "data": data
        })
    return result

# 실행 명령
# 터미널에서 실행: uvicorn exceltoweb:app --reload --host 12.52.146.94 --port 7000

if __name__ == "__main__":
    uvicorn.run("exceltoweb:app", host="12.52.146.94", port=7000)
