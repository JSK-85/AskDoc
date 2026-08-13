import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
            
        tree = ET.XML(xml_content)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        texts = []
        for node in tree.findall('.//w:t', ns):
            if node.text:
                texts.append(node.text)
                
        return '\n'.join(texts)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    text = extract_text_from_docx('/Users/jassi/Documents/QA/RAG_Backend_Spec_Antigravity.docx')
    with open('/Users/jassi/Documents/QA/RAG_Backend_Spec_Antigravity.txt', 'w') as f:
        f.write(text)
    print("Done")
