import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from bs4 import BeautifulSoup

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
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "해당 조건에 맞는 요소가 없습니다.")
            return

        extracted_texts = []
        for element in elements:
            text = element.get_text(strip=True)
            line = f"텍스트: {text}"
            
            if extract_links:
                # `a` 태그의 `href` 속성 추출
                a_tag = element.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    line += f" | 링크: {href}"
            
            if extract_images:
                # `img` 태그의 `src` 속성 추출
                img_tag = element.find('img', src=True)
                if img_tag:
                    src = img_tag['src']
                    line += f" | 이미지 경로: {src}"
            
            extracted_texts.append(line)
        
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "\n".join(extracted_texts))
    except Exception as e:
        messagebox.showerror("오류", f"텍스트 추출 중 오류가 발생했습니다:\n{e}")

def save_text():
    extracted = result_text.get(1.0, tk.END).strip()
    if not extracted:
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

# Tkinter 창 설정
root = tk.Tk()
root.title("HTML 텍스트 추출기")
root.geometry("800x700")

# HTML 내용 입력 섹션
html_frame = tk.LabelFrame(root, text="HTML 내용 붙여넣기")
html_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

html_text = scrolledtext.ScrolledText(html_frame, wrap=tk.WORD, height=15)
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
extract_button = tk.Button(root, text="텍스트 추출", command=extract_text)
extract_button.pack(pady=10)

# 결과 표시 섹션
result_frame = tk.LabelFrame(root, text="추출된 텍스트")
result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10, fg="green")
result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# 저장 버튼
save_button = tk.Button(root, text="추출된 텍스트 저장", command=save_text)
save_button.pack(pady=10)

# Tkinter 이벤트 루프 시작
root.mainloop()
