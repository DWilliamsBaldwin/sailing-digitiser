from pathlib import Path

import cv2
import numpy as np


RAW_DIR = Path("data/raw")
CORRECTED_DIR = Path("data/corrected")
DEBUG_DIR = Path("output/debug")

CORRECTED_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def rotate_image(image, angle):

    h, w = image.shape[:2]

    centre = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(
        centre,
        angle,
        1.0
    )

    rotated = cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def detect_lines(gray):

    edges = cv2.Canny(
        gray,
        50,
        150,
        apertureSize=3
    )

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=150,
        maxLineGap=20
    )

    return lines


def classify_lines(lines):

    horizontal = []
    vertical = []

    if lines is None:
        return horizontal, vertical

    for line in lines:

        line = np.array(line).flatten()

        if len(line) != 4:
            continue

        x1, y1, x2, y2 = line

        angle = np.degrees(
            np.arctan2(
                y2 - y1,
                x2 - x1
            )
        )

        if angle > 90:
            angle -= 180

        if angle < -90:
            angle += 180

        if abs(angle) < 15:
            horizontal.append(line)

        elif abs(abs(angle) - 90) < 15:
            vertical.append(line)

    return horizontal, vertical


def cluster_positions(
    positions,
    distance_threshold=10
):

    if len(positions) == 0:
        return []

    positions = sorted(positions)

    clusters = []

    current_cluster = [positions[0]]

    for pos in positions[1:]:

        if abs(
            pos - current_cluster[-1]
        ) <= distance_threshold:

            current_cluster.append(pos)

        else:

            clusters.append(
                int(
                    np.mean(current_cluster)
                )
            )

            current_cluster = [pos]

    clusters.append(
        int(
            np.mean(current_cluster)
        )
    )

    return clusters


def deduplicate_positions(
    positions,
    min_spacing
):

    if len(positions) == 0:
        return []

    positions = sorted(positions)

    result = [positions[0]]

    for pos in positions[1:]:

        if pos - result[-1] >= min_spacing:

            result.append(pos)

    return result


def get_grid_positions(
    horizontal_lines,
    vertical_lines
):

    row_candidates = []

    for line in horizontal_lines:

        x1, y1, x2, y2 = line

        row_candidates.append(
            int((y1 + y2) / 2)
        )

    column_candidates = []

    for line in vertical_lines:

        x1, y1, x2, y2 = line

        column_candidates.append(
            int((x1 + x2) / 2)
        )

    row_positions = cluster_positions(
        row_candidates,
        distance_threshold=8
    )
    
    column_positions = cluster_positions(
        column_candidates,
        distance_threshold=8
    )

    if len(row_positions) > 2:
    
        row_spacing = np.median(
            np.diff(row_positions)
        )
    
        row_positions = (
            deduplicate_positions(
                row_positions,
                min_spacing=row_spacing * 0.5
            )
        )
    
    if len(column_positions) > 2:
    
        column_spacing = np.median(
            np.diff(column_positions)
        )
    
        column_positions = (
            deduplicate_positions(
                column_positions,
                min_spacing=column_spacing * 0.5
            )
        )

    return (
        row_positions,
        column_positions
    )


def estimate_rotation(horizontal_lines):

    if len(horizontal_lines) == 0:
        return 0.0

    angles = []

    for line in horizontal_lines:

        x1, y1, x2, y2 = line

        angle = np.degrees(
            np.arctan2(
                y2 - y1,
                x2 - x1
            )
        )

        if angle > 90:
            angle -= 180

        if angle < -90:
            angle += 180

        angles.append(angle)

    return np.median(angles)


def draw_grid_positions(
    image,
    row_positions,
    column_positions
):

    output = image.copy()

    for y in row_positions:

        cv2.line(
            output,
            (0, y),
            (image.shape[1], y),
            (0, 0, 255),
            2
        )

    for x in column_positions:

        cv2.line(
            output,
            (x, 0),
            (x, image.shape[0]),
            (0, 255, 0),
            2
        )

    return output


def draw_lines(
    image,
    horizontal_lines,
    vertical_lines
):

    output = image.copy()

    for line in horizontal_lines:

        x1, y1, x2, y2 = line

        cv2.line(
            output,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            (0, 0, 255),
            2
        )

    for line in vertical_lines:

        x1, y1, x2, y2 = line

        cv2.line(
            output,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            (0, 255, 0),
            2
        )

    return output


def process_image(image_path):

    print(f"\nProcessing {image_path.name}")

    image = cv2.imread(str(image_path))

    if image is None:
        print("Could not read image")
        return

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    lines = detect_lines(gray)
    
    horizontal_lines, vertical_lines = classify_lines(
        lines
    )
    
    print(
        f"Horizontal: {len(horizontal_lines)}"
    )
    
    print(
        f"Vertical: {len(vertical_lines)}"
    )
    
    angle = estimate_rotation(
        horizontal_lines
    )

    print(
        f"Estimated angle: {angle:.2f} degrees"
    )

    row_positions, column_positions = (
        get_grid_positions(
            horizontal_lines,
            vertical_lines
        )
    )
    
    print(
        f"Rows: {len(row_positions)}"
    )
    
    print(
        f"Columns: {len(column_positions)}"
    )
    
    debug_lines = draw_grid_positions(
        image,
        row_positions,
        column_positions
    )

    debug_path = (
        DEBUG_DIR /
        f"{image_path.stem}_lines.jpg"
    )

    cv2.imwrite(
        str(debug_path),
        debug_lines
    )

    if abs(angle) > 45:
    
        if angle > 0:
    
            corrected = cv2.rotate(
                image,
                cv2.ROTATE_90_CLOCKWISE
            )
    
        else:
    
            corrected = cv2.rotate(
                image,
                cv2.ROTATE_90_COUNTERCLOCKWISE
            )
    
    else:
    
        corrected = rotate_image(
            image,
            angle
        )

    corrected_path = (
        CORRECTED_DIR /
        f"{image_path.stem}_deskewed.jpg"
    )

    cv2.imwrite(
        str(corrected_path),
        corrected
    )


def main():

    files = []

    files.extend(
        RAW_DIR.glob("*.jpg")
    )

    files.extend(
        RAW_DIR.glob("*.jpeg")
    )

    files.extend(
        RAW_DIR.glob("*.png")
    )

    print(
        f"Found {len(files)} images"
    )

    for image_file in files:
        process_image(image_file)


if __name__ == "__main__":
    main()