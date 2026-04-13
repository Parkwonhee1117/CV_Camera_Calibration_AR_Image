import cv2 as cv
import numpy as np

# =========================
# 1. 설정
# =========================
VIDEO_PATH = "Camera_Calibration_Test_Video_1.mp4"
IMAGE_PATH = "AR_Image.png"

board_pattern = (10, 7)
square_size = 0.025

FRAME_SKIP = 10
MAX_SAMPLES = 60

# =========================
# 2. Calibration
# =========================
objp = np.zeros((board_pattern[0]*board_pattern[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:board_pattern[0], 0:board_pattern[1]].T.reshape(-1, 2)
objp *= square_size

objpoints = []
imgpoints = []

cap = cv.VideoCapture(VIDEO_PATH)

frame_idx = 0
collected = 0

print("=== Collecting calibration frames ===")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_idx += 1

    if frame_idx % FRAME_SKIP != 0:
        continue

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    found, corners = cv.findChessboardCorners(gray, board_pattern, None)

    if found:
        objpoints.append(objp)
        imgpoints.append(corners)
        collected += 1

        cv.drawChessboardCorners(frame, board_pattern, corners, found)
        print(f"Collected: {collected}")

        cv.imshow("Corners", frame)
        cv.waitKey(100)

        if collected >= MAX_SAMPLES:
            break
    else:
        cv.imshow("Corners", frame)
        cv.waitKey(1)

cap.release()
cv.destroyAllWindows()

# =========================
# 3. Camera Calibration
# =========================
print("\n=== Calibration ===")

ret, K, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

print("K:\n", K)
print("dist:\n", dist)

# =========================
# 4. AR (3D 느낌 + 안정화)
# =========================
print("\n=== AR Visualization ===")

overlay = cv.imread(IMAGE_PATH, cv.IMREAD_UNCHANGED)

if overlay is None:
    print("이미지 로드 실패!")
    exit()

# 🔥 뒤집힘 해결
overlay = cv.flip(overlay, 0)

# 알파 처리
if overlay.shape[2] == 4:
    overlay_img = overlay[:, :, :3]
    overlay_mask = overlay[:, :, 3]
else:
    overlay_img = overlay
    gray_img = cv.cvtColor(overlay, cv.COLOR_BGR2GRAY)
    _, overlay_mask = cv.threshold(gray_img, 1, 255, cv.THRESH_BINARY)

h_img, w_img = overlay_img.shape[:2]

cap = cv.VideoCapture(VIDEO_PATH)

# corner refinement 설정
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    found, corners = cv.findChessboardCorners(gray, board_pattern, None)

    if found:
        # 🔥 코너 정밀화 (안정화 핵심)
        corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)

        # 🔥 Pose Estimation
        _, rvec, tvec = cv.solvePnP(
            objp, corners2, K, dist,
            flags=cv.SOLVEPNP_ITERATIVE
        )

        # 🔥 뒤집힘 방지 (카메라 뒤 제거)
        if tvec[2] <= 0:
            continue

        # =========================
        # 3D 평면 생성
        # =========================
        scale = 0.0001  # 🔥 중요 (너무 크면 깨짐)

        w = w_img * scale
        h = h_img * scale

        plane_3d = np.float32([
            [0, 0, 0],
            [w, 0, 0],
            [w, 0, -h],
            [0, 0, -h]
        ])

        # 👉 위치 조정 (중앙)
        plane_3d += np.array([2*square_size, 2*square_size, 0], dtype=np.float32)

        # =========================
        # 투영
        # =========================
        imgpts, _ = cv.projectPoints(plane_3d, rvec, tvec, K, dist)
        imgpts = imgpts.reshape(-1, 2)

        # =========================
        # Homography
        # =========================
        src_pts = np.array([
            [0, 0],
            [w_img, 0],
            [w_img, h_img],
            [0, h_img]
        ], dtype=np.float32)

        dst_pts = np.array(imgpts, dtype=np.float32)

        H, _ = cv.findHomography(src_pts, dst_pts)

        warped_img = cv.warpPerspective(
            overlay_img, H, (frame.shape[1], frame.shape[0])
        )

        warped_mask = cv.warpPerspective(
            overlay_mask, H, (frame.shape[1], frame.shape[0])
        )

        # =========================
        # 합성
        # =========================
        mask_inv = cv.bitwise_not(warped_mask)

        bg = cv.bitwise_and(frame, frame, mask=mask_inv)
        fg = cv.bitwise_and(warped_img, warped_img, mask=warped_mask)

        frame = cv.add(bg, fg)

    cv.imshow("3D Character AR (Stable)", frame)

    if cv.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()