import cv2
import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import watershed


def flatten(nested_list):
    flattened = [item for sublist in nested_list for item in sublist]
    return flattened

def mask_to_polygons(mask: np.ndarray, erosion: bool=True, use_watershed: bool=True, use_hierarchy: bool=False,
                     use_approximation: bool=True, minimum_distance:int=100):
    """
    Transform mask to several polygons detecting them using image processing.
    There are three developed possibilities to separate the polygons:
    - Watershed & hierarchy = False: this is the simplest method. In this method, the algorithm finds external contours
    of all polygons and add them into an array which gathers all polygons. It does not work properly in this case
    because background inside polygon is represented as polygon.
    - Use hierarchy: the aim of this technique is to identify all polygons detected by the method find contours. This
    method will separate background inner polygons and object polygons.
    - Use erosion: erode mask surface to remove inner background holes.
    - Use approximation: find approximation between polygon points to reduce the complexity of the polygons.
    :param mask: binary 2D mask
    :param erosion: boolean which indicates if we use the erosion method.
    :param use_watershed: boolean which indicates if we use the watershed method.
    :param minimum_distance: minimum distance parameter used for watershed algorithm.
    :return: list of polygons.
    """
    binary_mask = mask
    polygons = []

    if use_hierarchy:
        contours, hierarchies = cv2.findContours(binary_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        # documentation on hierarchy -> https://stackoverflow.com/questions/11782147/python-opencv-contour-tree-hierarchy-structure
        # https://stackoverflow.com/questions/48571526/how-can-i-get-rid-of-internal-contours-python

        hierarchies = hierarchies[0]
        for contour, hierarchy in zip(contours, hierarchies):
            next_item, previous, first_child, parent = hierarchy

            # Has no parent, which means it is not a hole
            if parent < 0:
                if first_child == -1:
                    polygon = contour.squeeze().tolist()
                    polygons.append(polygon)

                else:
                    polygon = contour.squeeze().tolist()

            else:
                polygon.extend(contour.squeeze().tolist())

                if next_item == -1:
                    polygons.append(polygon)

    else:
        if not use_watershed:
            if erosion:
                kernel = np.ones((3, 3), np.uint8)
                binary_mask = cv2.erode(binary_mask, kernel, iterations=10)

            # Find external contours from the binary mask
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_NONE)

            for contour in contours:
                polygon = contour.squeeze().tolist()
                polygons.append(polygon)

        else:
            distance = ndimage.distance_transform_edt(binary_mask)

            coords = peak_local_max(distance, min_distance=minimum_distance, labels=binary_mask)
            mask = np.zeros(distance.shape, dtype=bool)
            mask[tuple(coords.T)] = True

            markers, _ = ndimage.label(mask)
            labels = watershed(-distance, markers, mask=binary_mask)

            for label in np.unique(labels):
                # if the label is zero, we are examining the 'background' so simply ignore it
                if label == 0:
                    continue

                # otherwise, allocate memory for the label region and draw it on the mask
                mask = np.zeros(binary_mask.shape, dtype="uint8")
                mask[labels == label] = 255

                if use_approximation:

                    contour, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)

                    # Approximate the contour to reduce the number of points
                    # epsilon = 0.0001 * cv2.arcLength(contour[0], True)
                    # approx = cv2.approxPolyDP(contour[0], epsilon, True)

                    approx = contour[0]

                    # Convert the contour points to a list of tuples
                    polygon = approx.squeeze().tolist()

                else:
                    contour, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                                  cv2.CHAIN_APPROX_NONE)
                    polygon = contour[0].squeeze().tolist()

                polygons.append(polygon)

    return polygons

