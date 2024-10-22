import json
import os

import cv2
import numpy as np
from dotenv import load_dotenv
from picsellia import Client
from picsellia.types.enums import ImportAnnotationMode
from tqdm import tqdm

from mask_to_polygon import mask_to_polygons, flatten
from utils import bitmap_to_array, create_empty_coco_file

if __name__ == "__main__":
    load_dotenv()

    # create COCO annotation file
    CATEGORIES = ['alive', 'dead']
    coco_format = create_empty_coco_file(classes=CATEGORIES)

    direct_transfer = True
    dataset_version_id = os.getenv('DATASET_VERSION_ID')
    client = Client(api_token=os.getenv('PICSELLIA_TOKEN'), organization_name=os.getenv('ORGANIZATION_NAME'))
    dataset_version = client.get_dataset_version_by_id(dataset_version_id)


    mask_folder_path = 'mask_example_sample'  # Update with your mask folder path
    output_json_path = r'output\annotation_coco_sample.json'

    if direct_transfer:
        dataset_version.delete_all_annotations()

    for index_mask, mask_name in tqdm(enumerate(os.listdir(mask_folder_path))):
        json_filename = os.path.join(mask_folder_path, mask_name)

        try:
            with open(json_filename, 'r') as f:
                data = json.load(f)
            f.close()

            annotation_id = 1

            for index, label in enumerate(data["objects"]):
                bitmap = label["bitmap"]
                # function to compute the numpy arrays
                mask = bitmap_to_array(bitmap=bitmap, img_size=(data["size"]["height"], data["size"]["width"]))

                polygons = mask_to_polygons(mask, erosion=False, use_watershed=True, use_hierarchy=False,
                     use_approximation=False, minimum_distance=100)

                if index == 0:
                    # Add image information
                    image_filename = os.path.basename(json_filename).replace("_mask.jpg.json", ".jpg")
                    coco_format['images'].append({
                        'file_name': image_filename,
                        'height': mask.shape[0],
                        'width': mask.shape[1],
                        'id': index_mask + 1
                    })

                for polygon in polygons:
                    if len(polygon) >= 3:
                        x, y, w, h = cv2.boundingRect(np.array(polygon))
                        polygon_flatten = flatten(polygon)
                        annotation = {
                            'id': annotation_id,
                            'image_id': index_mask + 1,
                            'category_id': 1 if label["classTitle"] == "living" else 2,
                            'segmentation': [polygon_flatten],
                            'area': cv2.contourArea(np.array(polygon)),
                            'bbox': [x, y, w, h],
                            'iscrowd': 0
                        }
                        coco_format['annotations'].append(annotation)
                        annotation_id += 1

            if direct_transfer:
                with open(output_json_path, 'w') as json_file:
                    json.dump(coco_format, json_file, indent=4)
                json_file.close()

                dataset_version.import_annotations_coco_file(
                    file_path=output_json_path, mode = ImportAnnotationMode.KEEP,
                force_create_label= True, fail_on_asset_not_found = True)

                coco_format = create_empty_coco_file(classes=CATEGORIES)


        except Exception as e:
            print(f"JSON exception for {json_filename}, {str(e)}")

    if not direct_transfer:
        # Save the annotations to a JSON file
        with open(output_json_path, 'w') as json_file:
            json.dump(coco_format, json_file, indent=4)
        json_file.close()

    print(f"COCO format annotations saved to {output_json_path}")



