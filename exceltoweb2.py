from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import List, Any
import uvicorn

app = FastAPI()

# JSON 저장 경로 설정 (절대경로)
SAVE_PATH = r"C:\Workspace\saved_json"
os.makedirs(SAVE_PATH, exist_ok=True)

# CORS 설정 (필요 시)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 형식을 지정하는 모델 정의
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
        <title>Excel-like JSON Saver</title>
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
            <h3>웹 Excel 형태 - JSON 저장 및 불러오기</h3>
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
                    const response = await fetch(`/json/${filename}`);
                    if (response.ok) {
                        const list_of_dicts = await response.json();
                        if (list_of_dicts.length === 0) {
                            alert("빈 파일입니다.");
                            return;
                        }
                        const headers = Object.keys(list_of_dicts[0]);
                        const data = list_of_dicts.map(obj => headers.map(header => obj[header]));
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
# JSON으로 저장 엔드포인트
@app.post("/save")
async def save_data(data_model: DataModel, filename: str = Query(None)):
    # 파일 이름이 지정되지 않은 경우 기본 파일 이름 생성
    if not filename:
        filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        # 파일 이름에 .json 확장자가 없으면 추가
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
    
    file_path = os.path.join(SAVE_PATH, filename)
    
    # headers와 data를 [{}, {}, {}] 형식으로 변환
    headers = data_model.headers
    data = data_model.data
    list_of_dicts = [dict(zip(headers, row)) for row in data]
    
    # 파일 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(list_of_dicts, f, ensure_ascii=False, indent=2)
    
    # 저장된 파일 링크 생성
    file_link = f"/json/{filename}"
    return JSONResponse(content={"link": file_link})

# JSON 파일 접근용 엔드포인트
@app.get("/json/{filename}")
async def get_json(filename: str):
    file_path = os.path.join(SAVE_PATH, filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)  # [{}, {}, {}]
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "파일을 찾을 수 없습니다."}, status_code=404)

# JSON 파일 목록 제공 엔드포인트
@app.get("/list_json")
async def list_json_files():
    files = [f for f in os.listdir(SAVE_PATH) if f.endswith('.json')]
    return JSONResponse(content=files)

# 실행 명령
# 터미널에서 실행: uvicorn exceltoweb:app --reload --host 12.52.147.157 --port 7000


# 실행 명령
# uvicorn main:app --reload --host 0.0.0.0 --port 7000
if __name__ == "__main__":
    uvicorn.run("exceltoweb:app", host="12.52.146.94", port=7000)                              
