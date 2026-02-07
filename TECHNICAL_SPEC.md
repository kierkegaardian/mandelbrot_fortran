# Technical Specification: Mandelbrot Generator

## 1. Architecture
The application is structured into modular components to separate the mathematical logic/main loop from the input/output operations.

### Modules
1.  **`mod_ppm_writer`**: Handles the low-level binary writing of PPM image files.
2.  **`main`**:
    -   Defines the complex plane coordinates.
    -   Iterates over the pixel grid.
    -   Performs the Mandelbrot calculation ($Z_{n+1} = Z_n^2 + C$).
    -   Maps escape velocity to RGB colors.

## 2. Data Structures & Types
-   **Complex Numbers**: Uses `complex(kind=8)` (double precision complex) for accurate zooming.
-   **Image Buffer**: Due to potential large sizes, we may write row-by-row or allocate a 3D allocatable array `integer, allocatable :: image_data(:,:,:)`.

## 3. Algorithms
### Escape Time
For each pixel $C$:
1.  $Z = 0$
2.  Iterate $Z = Z^2 + C$ up to `MAX_ITER`.
3.  If $|Z| > 2.0$, the point has escaped.
4.  Color based on iteration count $i$.

### Julia Sets
When Julia mode is enabled:
1.  $Z$ starts at the pixel coordinate.
2.  $C$ is a constant specified by `julia_cx` and `julia_cy`.
3.  The same escape rule and coloring apply.

### Coloring
The default `rgb` palette uses a polynomial gradient for smooth ramps. The `gray` palette maps
normalized iteration counts linearly to 0-255.

### Smooth Coloring
Continuous potential is supported to reduce banding:
$$
\mu = i + 1 - \frac{\log(\log |Z|)}{\log 2}
$$
The normalized value $\mu / MAX\_ITER$ drives the gradient palette.

## 4. Output Format
**PPM (P6)**: Binary portable pixel map.
-   Header: `P6 <width> <height> 255`
-   Body: Binary RGB byte stream.
