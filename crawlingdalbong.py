import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from bs4 import BeautifulSoup
import webbrowser
import csv
import json
import pandas as pd

def extract_text():
    html_content = html_text.get(1.0, tk.END)
    tag = tag_entry.get().strip()
    class_name = class_entry.get().strip()
    extract_links = links_var.get()
    extract_images = images_var.get()

    if not tag:
        messagebox.showwarning("입력 부족", "태그 이름을 입력해주세요.")
        return

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        if class_name:
            elements = soup.find_all(tag, class_=class_name)
        else:
            elements = soup.find_all(tag)

        if not elements:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "해당 조건에 맞는 요소가 없습니다.")
            result_text.config(state=tk.DISABLED)
            return

        extracted_data.clear()
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)

        for idx, element in enumerate(elements, start=1):
            text = element.get_text(separator=' ', strip=True)
            line = f"요소 {idx}:\n  텍스트: {text}\n"
            
            links = []
            images = []

            if extract_links:
                a_tags = element.find_all('a', href=True)
                links = [a['href'] for a in a_tags]
                if links:
                    line += f"  링크:\n"
                    for link in links:
                        line += f"    - {link}\n"

            if extract_images:
                img_tags = element.find_all('img', src=True)
                images = [img['src'] for img in img_tags]
                if images:
                    line += f"  이미지 경로:\n"
                    for img in images:
                        line += f"    - {img}\n"

            extracted_data.append({
                '요소 번호': idx,
                '텍스트': text,
                '링크': links,
                '이미지 경로': images
            })

            # Insert text into Text widget with clickable links
            result_text.insert(tk.END, f"요소 {idx}:\n")
            result_text.insert(tk.END, f"  텍스트: {text}\n")

            if links:
                result_text.insert(tk.END, f"  링크:\n")
                for link in links:
                    link_start = result_text.index(tk.END)
                    result_text.insert(tk.END, f"    - {link}\n")
                    link_end = result_text.index(tk.END)
                    # Add tag for the link
                    tag_name = f"link{idx}_{links.index(link)}"
                    result_text.tag_add(tag_name, link_start, link_end)
                    result_text.tag_bind(tag_name, "<Button-1>", lambda e, url=link: open_url(url))
                    result_text.tag_config(tag_name, foreground="blue", underline=1)

            if images:
                result_text.insert(tk.END, f"  이미지 경로:\n")
                for img in images:
                    img_start = result_text.index(tk.END)
                    result_text.insert(tk.END, f"    - {img}\n")
                    img_end = result_text.index(tk.END)
                    # Add tag for the image
                    tag_name = f"image{idx}_{images.index(img)}"
                    result_text.tag_add(tag_name, img_start, img_end)
                    result_text.tag_bind(tag_name, "<Button-1>", lambda e, url=img: open_url(url))
                    result_text.tag_config(tag_name, foreground="blue", underline=1)

        result_text.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("오류", f"텍스트 추출 중 오류가 발생했습니다:\n{e}")

def open_url(url):
    webbrowser.open_new(url)

def save_text():
    extracted = result_text.get(1.0, tk.END).strip()
    if not extracted or extracted == "해당 조건에 맞는 요소가 없습니다.":
        messagebox.showwarning("저장 실패", "추출된 텍스트가 없습니다.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(extracted)
            messagebox.showinfo("성공", f"텍스트가 성공적으로 저장되었습니다:\n{file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"텍스트 저장 중 오류가 발생했습니다:\n{e}")

def save_structured_data():
    if not extracted_data:
        messagebox.showwarning("저장 실패", "추출된 데이터가 없습니다.")
        return

    file_type = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON 파일", "*.json"), ("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")]
    )
    if file_type:
        try:
            if file_type.endswith('.json'):
                with open(file_type, 'w', encoding='utf-8') as file:
                    json.dump(extracted_data, file, ensure_ascii=False, indent=4)
            elif file_type.endswith('.csv'):
                with open(file_type, 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['요소 번호', '텍스트', '링크', '이미지 경로'])
                    for data in extracted_data:
                        writer.writerow([
                            data['요소 번호'],
                            data['텍스트'],
                            "; ".join(data['링크']) if data['링크'] else "",
                            "; ".join(data['이미지 경로']) if data['이미지 경로'] else ""
                        ])
            elif file_type.endswith('.xlsx'):
                df = pd.DataFrame(extracted_data)
                # Convert lists to semicolon-separated strings for Excel
                df['링크'] = df['링크'].apply(lambda x: "; ".join(x) if x else "")
                df['이미지 경로'] = df['이미지 경로'].apply(lambda x: "; ".join(x) if x else "")
                df.to_excel(file_type, index=False)
            else:
                messagebox.showwarning("지원하지 않는 형식", "선택한 파일 형식을 지원하지 않습니다.")
                return
            messagebox.showinfo("성공", f"구조화된 데이터가 성공적으로 저장되었습니다:\n{file_type}")
        except Exception as e:
            messagebox.showerror("오류", f"데이터 저장 중 오류가 발생했습니다:\n{e}")

# 전역 변수로 추출된 데이터를 저장할 리스트
extracted_data = []

# Tkinter 창 설정
root = tk.Tk()
root.title("HTML 텍스트 추출기")
root.geometry("900x850")

# HTML 내용 입력 섹션
html_frame = tk.LabelFrame(root, text="HTML 내용 붙여넣기")
html_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

html_text = scrolledtext.ScrolledText(html_frame, wrap=tk.WORD, height=20)
html_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# 태그 및 클래스 입력 섹션
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tag_label = tk.Label(input_frame, text="태그 이름:")
tag_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

tag_entry = tk.Entry(input_frame, width=30)
tag_entry.grid(row=0, column=1, padx=5, pady=5)

class_label = tk.Label(input_frame, text="클래스 이름 (선택):")
class_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)

class_entry = tk.Entry(input_frame, width=30)
class_entry.grid(row=1, column=1, padx=5, pady=5)

# 추가 옵션 섹션
options_frame = tk.Frame(root)
options_frame.pack(pady=10)

links_var = tk.BooleanVar()
images_var = tk.BooleanVar()

links_check = tk.Checkbutton(options_frame, text="a href 링크 추출", variable=links_var)
links_check.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

images_check = tk.Checkbutton(options_frame, text="img src 이미지 경로 추출", variable=images_var)
images_check.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

# 추출 버튼
extract_button = tk.Button(root, text="텍스트 추출", command=extract_text, width=20, bg="lightblue")
extract_button.pack(pady=10)

# 결과 표시 섹션
result_frame = tk.LabelFrame(root, text="추출된 텍스트")
result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=25, fg="green")
result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
result_text.config(state=tk.DISABLED)

# 저장 버튼 섹션
save_buttons_frame = tk.Frame(root)
save_buttons_frame.pack(pady=10)

save_text_button = tk.Button(save_buttons_frame, text="추출된 텍스트 저장", command=save_text, width=20, bg="lightgreen")
save_text_button.grid(row=0, column=0, padx=10)

save_structured_button = tk.Button(save_buttons_frame, text="구조화된 데이터 저장", command=save_structured_data, width=20, bg="lightyellow")
save_structured_button.grid(row=0, column=1, padx=10)

# Tkinter 이벤트 루프 시작
root.mainloop()
