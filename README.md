# 📌 Camera Pose Estimation & AR

## 📖 프로젝트 개요

본 프로젝트는 OpenCV를 활용하여 카메라의 내부 파라미터를 추정하고, 체스보드 패턴을 기반으로 카메라의 자세(Pose)를 계산한 뒤, 이를 이용해 AR 객체를 영상 위에 시각화하는 것을 목표로 한다.

---

## 🎯 목표

* 카메라 캘리브레이션 수행
* 체스보드 패턴을 이용한 Pose Estimation
* 영상 위에 AR 객체(이미지)를 자연스럽게 표시

---

## ⚙️ 사용 기술

* OpenCV (cv2)
* Camera Calibration
* SolvePnP (Pose Estimation)
* Homography
* Image Warping (Perspective Transform)

---

## 🧩 구현 과정

### 1️⃣ Camera Calibration

체스보드 영상을 이용하여 카메라의 내부 파라미터(K)와 왜곡 계수(dist)를 추정하였다.

* 체스보드 패턴: `(10 x 7)`
* 각 정사각형 크기: `0.025m`

#### 주요 코드

```python
ret, K, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)
```

---

### 2️⃣ Pose Estimation (PnP)

체스보드의 3D 좌표와 이미지상의 2D 코너를 이용하여 카메라의 위치와 방향을 계산하였다.

#### 주요 코드

```python
_, rvec, tvec = cv.solvePnP(objp, corners, K, dist)
```

* `rvec`: 회전 벡터
* `tvec`: 이동 벡터

---

### 3️⃣ AR 객체 생성 (3D-like Image Plane)

단순한 2D overlay가 아닌, 3D 공간에 세워진 평면에 이미지를 매핑하여 보다 입체적으로 보이도록 구현하였다.

#### 3D 평면 정의

```python
plane_3d = np.float32([
    [0, 0, 0],
    [w, 0, 0],
    [w, 0, -h],
    [0, 0, -h]
])
```

---

### 4️⃣ Projection & Warping

3D 평면을 카메라 좌표계로 투영한 후, Homography를 이용하여 이미지가 해당 위치에 맞게 변형되도록 하였다.

#### Projection

```python
imgpts, _ = cv.projectPoints(plane_3d, rvec, tvec, K, dist)
```

#### Homography

```python
H, _ = cv.findHomography(src_pts, dst_pts)
warped_img = cv.warpPerspective(overlay_img, H, (frame.shape[1], frame.shape[0]))
```

---

### 5️⃣ 이미지 합성

Warp된 이미지와 원본 영상을 마스크를 이용해 합성하였다.

```python
frame = cv.add(bg, fg)
```

---

## 📸 결과

* 체스보드 위에 캐릭터 이미지가 AR 형태로 표시됨
* 카메라 움직임에 따라 자연스럽게 위치와 방향이 변함

<img width="1235" height="611" alt="스크린샷 2026-04-13 214316" src="https://github.com/user-attachments/assets/855c782b-2639-40dc-947a-df0812053ec0" />
<img width="1596" height="705" alt="스크린샷 2026-04-13 214322" src="https://github.com/user-attachments/assets/ce429da3-2107-42b6-836b-d04eb4e1661d" />

---

## ⚠️ 문제점 및 한계

### 1. 체스보드 검출 실패

일부 프레임에서 체스보드가 검출되지 않아 AR 객체가 사라지는 현상이 발생함.

### 2. Pose Estimation 불안정성

카메라 움직임이 빠르거나 영상이 흐릿한 경우, `solvePnP` 결과가 불안정해지는 문제가 있음.

### 3. 좌표계 차이로 인한 이미지 뒤집힘

이미지 좌표계와 3D 좌표계 차이로 인해 초기에는 이미지가 뒤집혀 출력되는 문제가 있었으며, 이를 보정함.

---

## 🚀 향후 개선 방향

* Pose Estimation 안정화를 위한 필터 적용 (Kalman Filter)
* 체스보드 대신 더 강건한 마커 사용 (ArUco Marker)
* 3D 모델 적용 (Open3D, VTK)
* 애니메이션 캐릭터 추가

---

## 🧠 결론

본 프로젝트를 통해 카메라 캘리브레이션부터 Pose Estimation, 그리고 AR 시각화까지의 전체 파이프라인을 구현하였다. 특히, 단순 2D overlay를 넘어서 3D 공간에 객체를 배치함으로써 보다 현실감 있는 AR 환경을 구성할 수 있었다.
