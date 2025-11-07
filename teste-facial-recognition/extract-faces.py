from mtcnn import MTCNN
from PIL import Image
from os import listdir
from os.path import isdir
from numpy import asarray

detector = MTCNN()

def extrair_face(arquivo,size=(160,160)):

    img = Image.open(arquivo) #caminho completo

    img = img.convert('RGB') #convertendo em rgb
    array = asarray(img)

    results = detector.detect_faces(array)

    x1, y1, width, height = results[0]['box']
    x2, y2 = x1 + width, y1 + height

    face = array[y1:y2, x1:x2]
    image = Image.fromarray(face)
    image = image.resize(size)

    return image

def flip_image(image):
    img = image.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def load_fotos(directory_src,directory_target):
    for filename in listdir(directory_src):
        path = directory_src + filename
        path_tg = directory_target + filename
        path_tg_flip = directory_target + "flip-" + filename

        try:
            face = extrair_face(path)

            flip = flip_image(face)

            face.save(path_tg, "JPEG", quality=100, optimize=True, progressive=True)
            flip.save(path_tg_flip, "JPEG", quality=100, optimize=True, progressive=True)
        except:
          print("Erro na imagem {}".format(path))


def load_dir(directory_src, directory_target):
    for subdir in listdir(directory_src):
        path = directory_src + subdir + "\\" #C:\Users\Camila\PycharmProjects\Autenticacao-Biometrica\teste-facial-recognition\rostos\fotos ou seja, de onde está tirando
        path_tg = directory_target + subdir + "\\" #C:\Users\Camila\PycharmProjects\Autenticacao-Biometrica\teste-facial-recognition\rostos\faces onde vai jogar

        if not  isdir(path):
            continue

        load_fotos(path,path_tg)

if __name__ == '__main__':
    load_dir("C:\\Users\\Camila\\PycharmProjects\\Autenticacao-Biometrica\\teste-facial-recognition\\rostos\\fotos\\",
            "C:\\Users\Camila\\PycharmProjects\Autenticacao-Biometrica\\teste-facial-recognition\\rostos\\faces\\"
             )