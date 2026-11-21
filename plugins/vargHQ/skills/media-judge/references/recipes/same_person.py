# Same face across two frames? OpenCV's YuNet finds it and SFace compares it. Cosine 0.363 or more means same person.
# usage: same_person.py a.jpg b.jpg yunet.onnx sface.onnx
import sys
import cv2

a, b = cv2.imread(sys.argv[1]), cv2.imread(sys.argv[2])
det = cv2.FaceDetectorYN.create(sys.argv[3], "", (320, 320), 0.7, 0.3, 50)
rec = cv2.FaceRecognizerSF.create(sys.argv[4], "")


def embed(img):
    det.setInputSize((img.shape[1], img.shape[0]))
    _, faces = det.detect(img)
    if faces is None:
        sys.exit("no face found")
    face = max(faces, key=lambda r: r[2])
    return rec.feature(rec.alignCrop(img, face))


cos = rec.match(embed(a), embed(b), cv2.FaceRecognizerSF_FR_COSINE)
print(f"cosine {cos:.3f}: {'same person' if cos >= 0.363 else 'different person'}")
