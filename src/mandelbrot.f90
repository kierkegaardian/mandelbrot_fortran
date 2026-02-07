program mandelbrot
  use mod_ppm_writer
  use mod_cli, only: render_config, parse_args, finalize_config, CLI_OK, CLI_HELP, CLI_ERROR
  use mod_cli, only: TYPE_MANDELBROT, TYPE_JULIA, TYPE_BURNINGSHIP, TYPE_TRICORN, TYPE_MULTIBROT, TYPE_CELTIC, TYPE_PERPENDICULAR
  use, intrinsic :: iso_c_binding, only: c_int
  use, intrinsic :: iso_fortran_env, only: int32, real64, error_unit
#ifdef _OPENMP
  use omp_lib
#endif
  implicit none

  interface
     subroutine c_exit(status) bind(C, name="exit")
       import :: c_int
       integer(c_int), value :: status
     end subroutine c_exit
  end interface

  ! Data
  type(render_config) :: cfg
  integer(int32), allocatable :: image_data(:,:,:) ! (3, width, height)
  integer :: cli_status, k
  real(real64) :: t_zoom, log_zoom, move_step
  character(len=512) :: filename
  character(len=512) :: cmd

  call parse_args(cfg, cli_status)
  select case (cli_status)
  case (CLI_OK)
     continue
  case (CLI_HELP)
     call c_exit(0_c_int)
  case default
     call c_exit(2_c_int)
  end select
  
  call finalize_config(cfg)

#ifdef _OPENMP
  if (cfg%threads > 0) call omp_set_num_threads(cfg%threads)
#endif
  
  write(error_unit, *) "Initializing Mandelbrot Generator..."
  
  allocate(image_data(3, cfg%width, cfg%height))

  if (cfg%video) then
      write(error_unit, *) "Video Mode Enabled"
      write(error_unit, *) "Frames:", cfg%frames
      write(error_unit, *) "Zoom:", cfg%zoom_start, "->", cfg%zoom_end
      write(error_unit, *) "Output Dir:", trim(cfg%output_dir)
      
      ! Create directory
      call execute_command_line("mkdir -p " // trim(cfg%output_dir), wait=.true.)
      
      do k = 1, cfg%frames
          ! Calculate zoom (logarithmic interpolation)
          if (cfg%frames > 1) then
              t_zoom = real(k - 1, real64) / real(cfg%frames - 1, real64)
          else
              t_zoom = 0.0_real64
          end if
          
          if (cfg%zoom_start <= 0.0_real64) cfg%zoom_start = 1.0_real64
          if (cfg%zoom_end <= 0.0_real64) cfg%zoom_end = 1.0_real64
          
          log_zoom = (1.0_real64 - t_zoom) * log(cfg%zoom_start) + t_zoom * log(cfg%zoom_end)
          cfg%zoom = exp(log_zoom)
          
          ! Recalculate bounds based on new zoom
          cfg%bounds_provided = .false. 
          call finalize_config(cfg)
          
          write(error_unit, *) "Rendering frame", k, "/", cfg%frames, "Zoom:", cfg%zoom
          call render_frame()
          
          write(filename, '(A,A,I4.4,A)') trim(cfg%output_dir), "/frame_", k, ".ppm"
          call write_ppm(trim(filename), cfg%width, cfg%height, image_data)
      end do
      write(error_unit, *) "Sequence complete. Convert to video with:"
      write(error_unit, *) "ffmpeg -framerate 30 -i ", trim(cfg%output_dir), "/frame_%04d.ppm -c:v libx264 -pix_fmt yuv420p video.mp4"

  else if (cfg%interactive) then
      write(error_unit, *) "Interactive Explorer Mode"
      write(error_unit, *) "Commands:"
      write(error_unit, *) "  w/a/s/d : Pan Up/Left/Down/Right"
      write(error_unit, *) "  + / -   : Zoom In/Out"
      write(error_unit, *) "  q       : Quit"
      write(error_unit, *) "  Enter   : Render current view"
      
      do
         call finalize_config(cfg)
         write(error_unit, *) "Rendering center=(", cfg%center_x, ",", cfg%center_y, ") zoom=", cfg%zoom
         call render_frame()
         call write_ppm("interactive.ppm", cfg%width, cfg%height, image_data)
         write(error_unit, *) "Rendered to interactive.ppm"
         
         write(error_unit, *) "Command?> "
         read(*, '(A)') cmd
         cmd = adjustl(cmd)
         
         if (trim(cmd) == 'q') exit
         
         ! Simple parsing
         move_step = 0.2_real64
         
         if (trim(cmd) == 'w') cfg%center_y = cfg%center_y - (cfg%y_max - cfg%y_min) * move_step
         if (trim(cmd) == 's') cfg%center_y = cfg%center_y + (cfg%y_max - cfg%y_min) * move_step
         if (trim(cmd) == 'a') cfg%center_x = cfg%center_x - (cfg%x_max - cfg%x_min) * move_step
         if (trim(cmd) == 'd') cfg%center_x = cfg%center_x + (cfg%x_max - cfg%x_min) * move_step
         if (trim(cmd) == '+') cfg%zoom = cfg%zoom * 1.5_real64
         if (trim(cmd) == '-') cfg%zoom = cfg%zoom / 1.5_real64
         
         cfg%bounds_provided = .false.
      end do

  else
      ! Single image mode
      write(error_unit, *) "Resolution:", cfg%width, "x", cfg%height
      write(error_unit, *) "Plane: x=[", cfg%x_min, ",", cfg%x_max, "] y=[", cfg%y_min, ",", cfg%y_max, "]"
      
      call print_mode_info()
      write(error_unit, *) "Calculating..."
      
      call render_frame()
      
      write(error_unit, *) "Writing to file..."
      call write_ppm(trim(cfg%output), cfg%width, cfg%height, image_data)
      write(error_unit, *) "Done! Output saved to ", trim(cfg%output)
  end if
  
  deallocate(image_data)

contains

  subroutine print_mode_info()
      select case (cfg%fractal_type)
      case (TYPE_JULIA)
         write(error_unit, *) "Mode: Julia (c = ", cfg%julia_cx, ", ", cfg%julia_cy, ")"
      case (TYPE_BURNINGSHIP)
         write(error_unit, *) "Mode: Burning Ship"
      case (TYPE_TRICORN)
         write(error_unit, *) "Mode: Tricorn"
      case (TYPE_MULTIBROT)
         write(error_unit, *) "Mode: Multibrot (power=", cfg%power, ")"
      case (TYPE_CELTIC)
         write(error_unit, *) "Mode: Celtic Mandelbrot"
      case (TYPE_PERPENDICULAR)
         write(error_unit, *) "Mode: Perpendicular Mandelbrot"
      case default
         write(error_unit, *) "Mode: Mandelbrot"
      end select

      if (cfg%cyclic) then
         write(error_unit, *) "Coloring: cyclic (freq=", cfg%cycle_freq, ")"
      else if (cfg%smooth) then
         write(error_unit, *) "Coloring: smooth"
      end if
  end subroutine print_mode_info

  subroutine render_frame()
    integer :: i, j, iter
    real(real64) :: x0, y0, dx, dy
    complex(real64) :: c, z, julia_c
    logical :: show_progress

    if (cfg%width > 1) then
       dx = (cfg%x_max - cfg%x_min) / real(cfg%width - 1, real64)
    else
       dx = 0.0_real64
    end if
    if (cfg%height > 1) then
       dy = (cfg%y_max - cfg%y_min) / real(cfg%height - 1, real64)
    else
       dy = 0.0_real64
    end if

    show_progress = (cfg%progress_every > 0 .and. .not. cfg%video .and. .not. cfg%interactive)
    julia_c = cmplx(cfg%julia_cx, cfg%julia_cy, kind=real64)

#ifdef _OPENMP
    if (omp_get_max_threads() > 1) show_progress = .false.
!$omp parallel do default(none) shared(cfg,image_data,dx,dy,show_progress,julia_c) private(j,i,y0,x0,c,z,iter) schedule(dynamic)
#endif
    do j = 1, cfg%height
       if (show_progress) then
          if (mod(j, cfg%progress_every) == 0) then
             write(error_unit, *) "Row ", j, " / ", cfg%height
          end if
       end if

       y0 = cfg%y_min + real(j - 1, real64) * dy

       do i = 1, cfg%width
          x0 = cfg%x_min + real(i - 1, real64) * dx

          if (cfg%fractal_type == TYPE_JULIA) then
             z = cmplx(x0, y0, kind=real64)
             c = julia_c
          else
             c = cmplx(x0, y0, kind=real64)
             z = cmplx(0.0_real64, 0.0_real64, kind=real64)
          end if

          iter = 0
          do while ((abs(z) <= 2.0_real64) .and. (iter < cfg%max_iter))
             select case (cfg%fractal_type)
             case (TYPE_BURNINGSHIP)
                z = cmplx(abs(real(z)), abs(aimag(z)), kind=real64)**2 + c
             case (TYPE_TRICORN)
                z = conjg(z)**2 + c
             case (TYPE_MULTIBROT)
                z = z**cfg%power + c
             case (TYPE_CELTIC)
                ! Celtic: |Re(z^2)| + i*Im(z^2) + c
                ! z*z gives z^2.
                z = cmplx(abs(real(z*z)), aimag(z*z), kind=real64) + c
             case (TYPE_PERPENDICULAR)
                ! Perpendicular: (Re(z) + i|Im(z)|)^2 + c
                z = cmplx(real(z), abs(aimag(z)), kind=real64)**2 + c
             case default
                z = z*z + c
             end select
             iter = iter + 1
          end do

          call color_pixel(iter, cfg%max_iter, cfg%palette, cfg%smooth, cfg%cyclic, cfg%cycle_freq, z, image_data(:, i, j))
       end do
    end do
#ifdef _OPENMP
!$omp end parallel do
#endif
  end subroutine render_frame

  subroutine color_pixel(iter, max_iter, palette, smooth, cyclic, freq, z, rgb)
    use, intrinsic :: iso_fortran_env, only: int32, real64
    integer, intent(in) :: iter, max_iter
    character(len=*), intent(in) :: palette
    logical, intent(in) :: smooth, cyclic
    real(real64), intent(in) :: freq
    complex(real64), intent(in) :: z
    integer(int32), intent(out) :: rgb(3)
    integer(int32) :: v
    character(len=16) :: p
    real(real64) :: t, smooth_iter, mag, two_pi
    real(real64) :: r, g, b

    if (iter >= max_iter) then
       rgb = 0_int32
       return
    end if

    if (smooth) then
       mag = abs(z)
       if (mag > 0.0_real64) then
          smooth_iter = real(iter, real64) + 1.0_real64 - log(log(mag)) / log(2.0_real64)
       else
          smooth_iter = real(iter, real64)
       end if
    else
       smooth_iter = real(iter, real64)
    end if

    if (cyclic) then
       ! Cyclic/Psychedelic coloring
       ! Map iteration count to a sine wave phase
       t = 0.5_real64 + 0.5_real64 * sin(freq * smooth_iter)
    else
       t = smooth_iter / real(max_iter, real64)
       t = max(0.0_real64, min(1.0_real64, t))
    end if

    p = adjustl(palette)
    two_pi = 2.0_real64 * acos(-1.0_real64)
    select case (trim(p))
    case ("gray")
       v = int(255.0_real64 * t, int32)
       v = max(0_int32, min(255_int32, v))
       rgb = v
    case ("sunset")
       r = 0.85_real64 * (0.5_real64 + 0.5_real64 * cos(two_pi * (t + 0.0_real64)))
       g = 0.55_real64 * (0.5_real64 + 0.5_real64 * cos(two_pi * (t + 0.15_real64)))
       b = 0.35_real64 * (0.5_real64 + 0.5_real64 * cos(two_pi * (t + 0.35_real64)))
       rgb(1) = max(0_int32, min(255_int32, int(255.0_real64 * r, int32)))
       rgb(2) = max(0_int32, min(255_int32, int(255.0_real64 * g, int32)))
       rgb(3) = max(0_int32, min(255_int32, int(255.0_real64 * b, int32)))
    case ("ice")
       r = 0.15_real64 + 0.25_real64 * (1.0_real64 - t)
       g = 0.35_real64 + 0.45_real64 * (1.0_real64 - t)
       b = 0.65_real64 + 0.35_real64 * (1.0_real64 - t)
       rgb(1) = max(0_int32, min(255_int32, int(255.0_real64 * r, int32)))
       rgb(2) = max(0_int32, min(255_int32, int(255.0_real64 * g, int32)))
       rgb(3) = max(0_int32, min(255_int32, int(255.0_real64 * b, int32)))
    case ("fire")
       r = min(1.0_real64, 3.0_real64 * t)
       g = min(1.0_real64, max(0.0_real64, 3.0_real64 * t - 1.0_real64))
       b = min(1.0_real64, max(0.0_real64, 3.0_real64 * t - 2.0_real64))
       rgb(1) = max(0_int32, min(255_int32, int(255.0_real64 * r, int32)))
       rgb(2) = max(0_int32, min(255_int32, int(255.0_real64 * g, int32)))
       rgb(3) = max(0_int32, min(255_int32, int(255.0_real64 * b, int32)))
    case default
       r = 9.0_real64 * t * (1.0_real64 - t) * (1.0_real64 - t) * (1.0_real64 - t)
       g = 15.0_real64 * t * t * (1.0_real64 - t) * (1.0_real64 - t)
       b = 8.5_real64 * t * t * t * (1.0_real64 - t)
       rgb(1) = max(0_int32, min(255_int32, int(255.0_real64 * r, int32)))
       rgb(2) = max(0_int32, min(255_int32, int(255.0_real64 * g, int32)))
       rgb(3) = max(0_int32, min(255_int32, int(255.0_real64 * b, int32)))
    end select
  end subroutine color_pixel

end program mandelbrot