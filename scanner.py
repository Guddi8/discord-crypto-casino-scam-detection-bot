import io, os, json, cv2, pdqhash
import numpy as np

def pdq_hash_from_path(path):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    bits, _ = pdqhash.compute(image)
    n = ((len(bits) + 7) // 8) * 8
    padded = np.pad(bits, (0, n - len(bits)), constant_values=0)
    bytes_arr = np.packbits(padded.reshape(-1, 8), axis=1, bitorder='big').flatten()
    return str(bytes_arr.tobytes().hex())



IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}


def find_image_paths(root):
    root = os.path.abspath(root)
    paths = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in IMAGE_EXTS:
                paths.append(os.path.join(dirpath, fn))
    return paths


with open("hashes.txt", "r") as f:
    hashes = f.read().splitlines()

for path in find_image_paths("./scan"):
    hash = pdq_hash_from_path(path)
    print(hash)
    hashes.append(hash)

with open("hashes.txt", "w") as f:
    f.write("\n".join(list(set(hashes))))
