import pyautogui
import cv2
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'F:\Programs\Tesseract-OCR\tesseract.exe'

substat_pos =  [(1162, 397),(1485, 397),(1164, 450),(1484, 450)]

def extract_text(img, config='--psm 7'):
    # Get OCR results with confidence values
    data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
    
    text_parts = []
    confidences = []

    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        conf = int(data['conf'][i])
        if word and conf > 0:  # Filter out empty or invalid results
            text_parts.append(word)
            confidences.append(conf)

    text = ' '.join(text_parts).lower()

    return text

def get_main_stat(img):
    cropped_img = img[301:301+45, 1164:1164+220]
    _, cropped_img = cv2.threshold(cropped_img, 190, 255, cv2.THRESH_BINARY)
    cropped_img = cv2.bitwise_not(cropped_img)

    cv2.imwrite('res\\main_stat_0.png', cropped_img)
    main_text = extract_text(cropped_img, config='--psm 6')

    cropped_img = img[301:301+45, 1164+220:1164+300]
    _, cropped_img = cv2.threshold(cropped_img, 190, 255, cv2.THRESH_BINARY)
    cropped_img = cv2.bitwise_not(cropped_img)

    cv2.imwrite(f'res\\main_stat_1.png', cropped_img)
    num_text = extract_text(cropped_img, config='--psm 7')
    return main_text+' '+num_text
 
def get_sub_stat(img, index):
    cropped_img = img[substat_pos[index][1]:substat_pos[index][1]+45, substat_pos[index][0]:substat_pos[index][0]+200]
    _, cropped_img = cv2.threshold(cropped_img, 190, 255, cv2.THRESH_BINARY)
    cropped_img = cv2.bitwise_not(cropped_img)

    cv2.imwrite(f'res\\sub_stat_{index}_0.png', cropped_img)
    sub_text = extract_text(cropped_img, config='--psm 6')
    
    if sub_text == '': 
        return ''

    cropped_img = img[substat_pos[index][1]:substat_pos[index][1]+45, substat_pos[index][0]+200:substat_pos[index][0]+300]
    _, cropped_img = cv2.threshold(cropped_img, 190, 255, cv2.THRESH_BINARY)
    cropped_img = cv2.bitwise_not(cropped_img)

    cv2.imwrite(f'res\\sub_stat_{index}_1.png', cropped_img)
    num_text = extract_text(cropped_img, config='--psm 7')
    return sub_text+' '+num_text

def get_disk_title(img, margin=2):
    cropped_img = img[122:164, 89:1043]
    _, cropped_img = cv2.threshold(cropped_img, 125, 255, cv2.THRESH_BINARY)
    
    coords = cv2.findNonZero(cropped_img)
    x, y, w, h = cv2.boundingRect(coords)
    y1 = max(y - margin, 0)
    y2 = min(y + h + margin, img.shape[0])
    x1 = max(x - margin, 0)
    x2 = min(x + w + margin, img.shape[1])

    cropped_img = cv2.bitwise_not(cropped_img)
    cropped_img = cropped_img[y1:y2, x1:x2]

    cropped_img = cv2.bilateralFilter(cropped_img, d=5, sigmaColor=75, sigmaSpace=75)
    cropped_img = cv2.dilate(cropped_img,np.ones((3,3),np.uint8),iterations = 1)

    cv2.imwrite(f'res\\title.png', cropped_img)
    text = extract_text(cropped_img, config='--psm 7')
    return text

def get_num_disks(img):
    cropped_img = img[124:157, 320:500]
    _, cropped_img = cv2.threshold(cropped_img, 125, 255, cv2.THRESH_BINARY)
    cropped_img = cv2.bitwise_not(cropped_img)

    cropped_img = cv2.bilateralFilter(cropped_img, d=5, sigmaColor=75, sigmaSpace=75)
    cropped_img = cv2.bilateralFilter(cropped_img, d=5, sigmaColor=75, sigmaSpace=75)

    cv2.imwrite(f'res\\storage.png', cropped_img)
    text = extract_text(cropped_img, config='--psm 6')
    # print(text)
    return text

def is_trashed(img):
    return img[825, 1445] < 127

def is_locked(img):
    return img[835, 1519] < 127

if __name__ == "__main__":

    # Take screenshot and convert to grayscale
    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # print(is_trashed(img))
    # print(is_locked(img))

    # Run extraction
    print(get_num_disks(img))
    print(get_disk_title(img))
    # print(get_main_stat(img))
    # print(get_sub_stat(img, 0))
    # print(get_sub_stat(img, 1))
    # print(get_sub_stat(img, 2))
    # print(get_sub_stat(img, 3))