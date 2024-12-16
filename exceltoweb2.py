from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import json
import os
from datetime import datetime
from typing import List, Any
import uvicorn
app = FastAPI()
# JSON 저장 경로 설정 (절대경로 사용)
SAVE_PATH = r"C:\Workspace\saved_json"
os.makedirs(SAVE_PATH, exist_ok=True)
# CORS 설정 (필요 시)
from fastapi.middleware.cors import CORSMiddleware
# CORS 설정
origins = [
    "http://12.52.146.94:7000",
    "http://127.0.0.1:7000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 개발 중에는 "*"로 설정 가능, 프로덕션에서는 특정 출처로 제한
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
        <title>Tabulator JSON Saver</title>
        <!-- Tabulator CSS CDN 링크 -->
        <link href="https://unpkg.com/tabulator-tables@5.4.4/dist/css/tabulator.min.css" rel="stylesheet">
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
                <button ON-CLICK="saveData()">저장</button>
                <select id="jsonFiles">
                    <option value="">-- 파일 선택 --</option>
                </select>
                <button ON-CLICK="loadData()">불러오기</button>
            </div>
        </div>
        
        <div id="controls">
            <button ON-CLICK="addRow()">행 추가</button>
            <button ON-CLICK="addColumn()">열 추가</button>
        </div>
        
        <div id="excel"></div>
        
        <!-- Tabulator JS CDN 링크 -->
        <script src="https://unpkg.com/tabulator-tables@5.4.4/dist/js/tabulator.min.js"></script>
        <script>
            // Tabulator 테이블 초기화
            let table = new Tabulator("#excel", {
                data: [], // 초기 데이터 빈 배열
                layout:"fitColumns",
                responsiveLayout:"hide",
                addRowPos:"top",
                history:true,
                pagination:"local",
                paginationSize:10,
                movableColumns:true,
                resizableRows:true,
                columnSorting:true,
                columns:[
                    {title:"A", field:"A", editor:"input"},
                    {title:"B", field:"B", editor:"input"},
                    {title:"C", field:"C", editor:"input"},
                ],
                cellEdited:function(cell){
                    // 셀이 편집될 때마다 호출됩니다. 필요 시 추가 기능 구현 가능
                },
            });
            // 페이지 로드 시 JSON 파일 목록 가져오기
            window.ON-LOAD = async function() {
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
                const headers = table.getColumns().map(col => col.getDefinition().title);
                const data = table.getData();  // Tabulator의 데이터 가져오기
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
                        const data = list_of_dicts.map(obj => {
                            let row = {};
                            headers.forEach(header => {
                                row[header] = obj[header];
                            });
                            return row;
                        });
                        // Tabulator의 열 헤더 설정
                        table.setColumns(headers.map(header => ({title: header, field: header, editor: "input"})));
                        // Tabulator에 데이터 로드
                        table.setData(data);
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
                table.addRow({});
            }
            function addColumn() {
                const currentColCount = table.getColumns().length;
                const newColTitle = `Column ${currentColCount + 1}`;
                const newField = `Col${currentColCount + 1}`;
                table.addColumn({title: newColTitle, field: newField, editor: "input"});
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
# 터미널에서 실행: uvicorn main:app --reload --host 0.0.0.0 --port 7000
if __name__ == "__main__":
    uvicorn.run("exceltoweb:app", host="12.52.146.94", port=7000)  # 포트 번호 5000으로 변경
