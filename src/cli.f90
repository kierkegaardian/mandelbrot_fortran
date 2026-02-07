module mod_cli
  use, intrinsic :: iso_fortran_env, only: real64, output_unit, error_unit
  implicit none
  private
  public :: render_config, parse_args, finalize_config, print_help
  public :: CLI_OK, CLI_HELP, CLI_ERROR
  public :: TYPE_MANDELBROT, TYPE_JULIA, TYPE_BURNINGSHIP, TYPE_TRICORN, TYPE_MULTIBROT, TYPE_CELTIC, TYPE_PERPENDICULAR

  integer, parameter :: CLI_OK = 0
  integer, parameter :: CLI_HELP = 1
  integer, parameter :: CLI_ERROR = 2

  integer, parameter :: TYPE_MANDELBROT = 0
  integer, parameter :: TYPE_JULIA = 1
  integer, parameter :: TYPE_BURNINGSHIP = 2
  integer, parameter :: TYPE_TRICORN = 3
  integer, parameter :: TYPE_MULTIBROT = 4
  integer, parameter :: TYPE_CELTIC = 5
  integer, parameter :: TYPE_PERPENDICULAR = 6

  type :: render_config
     integer :: width = 800
     integer :: height = 600
     integer :: max_iter = 255

     ! Bounds mode (explicit plane bounds). If not provided, we use center/zoom mode.
     logical :: bounds_provided = .false.
     real(real64) :: x_min = -2.0_real64
     real(real64) :: x_max =  1.0_real64
     real(real64) :: y_min = -1.2_real64
     real(real64) :: y_max =  1.2_real64

     ! Center/zoom mode
     real(real64) :: center_x = -0.5_real64
     real(real64) :: center_y =  0.0_real64
     real(real64) :: zoom = 1.0_real64

     character(len=256) :: output = "mandelbrot.ppm"
     character(len=16) :: palette = "rgb"
     integer :: progress_every = 50
     integer :: threads = 0
     logical :: smooth = .false.
     
     ! Fractal settings
     integer :: fractal_type = TYPE_MANDELBROT
     real(real64) :: power = 2.0_real64 ! For Multibrot
     
     ! Julia specific
     real(real64) :: julia_cx = -0.8_real64
     real(real64) :: julia_cy =  0.156_real64
     
     ! Advanced Coloring
     logical :: cyclic = .false.
     real(real64) :: cycle_freq = 0.1_real64

     ! Video/Zoom Sequence
     logical :: video = .false.
     integer :: frames = 60
     real(real64) :: zoom_start = 1.0_real64
     real(real64) :: zoom_end = 100.0_real64
     character(len=256) :: output_dir = "frames"
     
     ! Interactive
     logical :: interactive = .false.
  end type render_config

contains

  subroutine print_help(unit)
    integer, intent(in) :: unit
    write(unit, '(A)') "Fortran Mandelbrot Generator"
    write(unit, '(A)') ""
    write(unit, '(A)') "Usage:"
    write(unit, '(A)') "  ./mandelbrot_gen [options]"
    write(unit, '(A)') ""
    write(unit, '(A)') "Options:"
    write(unit, '(A)') "  --width N           Image width (default 800)"
    write(unit, '(A)') "  --height N          Image height (default 600)"
    write(unit, '(A)') "  --iter N            Max iterations (default 255)"
    write(unit, '(A)') "  --output PATH       Output PPM path (default mandelbrot.ppm)"
    write(unit, '(A)') "  --palette NAME      rgb|gray|sunset|ice|fire (default rgb)"
    write(unit, '(A)') "  --progress-every N  Print progress every N rows; 0 disables (default 50)"
    write(unit, '(A)') "  --threads N         OpenMP threads (requires build with OPENMP=1)"
    write(unit, '(A)') "  --smooth            Enable smooth coloring"
    write(unit, '(A)') "  --interactive       Start interactive explorer mode"
    write(unit, '(A)') ""
    write(unit, '(A)') "Fractal Modes:"
    write(unit, '(A)') "  --type NAME         mandelbrot|julia|ship|tricorn|multibrot (default mandelbrot)"
    write(unit, '(A)') "  --power N           Exponent for Multibrot (default 2.0)"
    write(unit, '(A)') ""
    write(unit, '(A)') "Julia Set options:"
    write(unit, '(A)') "  --julia             Shortcut for --type julia"
    write(unit, '(A)') "  --julia-cx X        Julia constant real component (default -0.8)"
    write(unit, '(A)') "  --julia-cy Y        Julia constant imag component (default 0.156)"
    write(unit, '(A)') ""
    write(unit, '(A)') "Coloring options:"
    write(unit, '(A)') "  --cyclic            Enable cyclic/psychedelic coloring"
    write(unit, '(A)') "  --freq F            Frequency for cyclic coloring (default 0.1)"
    write(unit, '(A)') ""
    write(unit, '(A)') "Video options:"
    write(unit, '(A)') "  --video             Generate a zoom sequence"
    write(unit, '(A)') "  --frames N          Number of frames (default 60)"
    write(unit, '(A)') "  --zoom-start Z      Start zoom level (default 1.0)"
    write(unit, '(A)') "  --zoom-end Z        End zoom level (default 100.0)"
    write(unit, '(A)') "  --output-dir DIR    Directory for frames (default 'frames')"
    write(unit, '(A)') ""
    write(unit, '(A)') "Bounds mode:"
    write(unit, '(A)') "  --xmin X --xmax X --ymin Y --ymax Y"
    write(unit, '(A)') ""
    write(unit, '(A)') "Center/zoom mode (used when bounds not given):"
    write(unit, '(A)') "  --center-x X --center-y Y --zoom Z"
    write(unit, '(A)') ""
    write(unit, '(A)') "Examples:"
    write(unit, '(A)') "  ./mandelbrot_gen --type ship --output ship.ppm"
    write(unit, '(A)') "  ./mandelbrot_gen --type multibrot --power 3 --palette ice"
    write(unit, '(A)') "  ./mandelbrot_gen --cyclic --freq 0.2 --palette fire"
    write(unit, '(A)') "  ./mandelbrot_gen --video --center-x -0.75 --frames 300 --zoom-end 10000"
  end subroutine print_help

  subroutine parse_args(cfg, status)
    type(render_config), intent(inout) :: cfg
    integer, intent(out) :: status

    integer :: argc, idx
    character(len=512) :: arg, key, val
    logical :: has_val

    status = CLI_OK
    argc = command_argument_count()

    idx = 1
    do while (idx <= argc)
       call get_command_argument(idx, arg)
       arg = adjustl(arg)

       if (arg == "--help" .or. arg == "-h") then
          call print_help(output_unit)
          status = CLI_HELP
          return
       end if
       if (arg == "--smooth") then
          cfg%smooth = .true.
          idx = idx + 1
          cycle
       end if
       if (arg == "--julia") then
          cfg%fractal_type = TYPE_JULIA
          idx = idx + 1
          cycle
       end if
       if (arg == "--cyclic") then
          cfg%cyclic = .true.
          idx = idx + 1
          cycle
       end if
       if (arg == "--video") then
          cfg%video = .true.
          idx = idx + 1
          cycle
       end if
       if (arg == "--interactive") then
          cfg%interactive = .true.
          idx = idx + 1
          cycle
       end if

       call split_kv(arg, key, val, has_val)

       if (.not. has_val) then
          if (idx == argc) then
             write(error_unit, '(A,A)') "Missing value for: ", trim(key)
             status = CLI_ERROR
             return
          end if
          idx = idx + 1
          call get_command_argument(idx, val)
       end if

       if (.not. apply_option(cfg, trim(key), trim(val))) then
          write(error_unit, '(A,A)') "Unknown or invalid option: ", trim(key)
          status = CLI_ERROR
          return
       end if

       idx = idx + 1
    end do
  end subroutine parse_args

  subroutine finalize_config(cfg)
    type(render_config), intent(inout) :: cfg
    real(real64) :: x_range, y_range, aspect

    if (.not. cfg%bounds_provided) then
       if (cfg%zoom <= 0.0_real64) cfg%zoom = 1.0_real64
       x_range = 3.0_real64 / cfg%zoom
       aspect = real(cfg%height, real64) / max(1.0_real64, real(cfg%width, real64))
       y_range = x_range * aspect

       cfg%x_min = cfg%center_x - 0.5_real64 * x_range
       cfg%x_max = cfg%center_x + 0.5_real64 * x_range
       cfg%y_min = cfg%center_y - 0.5_real64 * y_range
       cfg%y_max = cfg%center_y + 0.5_real64 * y_range
    end if

    if (cfg%width < 1) cfg%width = 1
    if (cfg%height < 1) cfg%height = 1
    if (cfg%max_iter < 1) cfg%max_iter = 1
    if (cfg%progress_every < 0) cfg%progress_every = 0
  end subroutine finalize_config

  subroutine split_kv(arg, key, val, has_val)
    character(len=*), intent(in) :: arg
    character(len=*), intent(out) :: key, val
    logical, intent(out) :: has_val
    integer :: p

    key = arg
    val = ""
    has_val = .false.

    p = index(arg, "=")
    if (p > 0) then
       key = arg(1:p-1)
       val = arg(p+1:)
       has_val = .true.
    end if
  end subroutine split_kv

  logical function apply_option(cfg, key, val)
    type(render_config), intent(inout) :: cfg
    character(len=*), intent(in) :: key, val
    integer :: ios

    apply_option = .true.

    select case (key)
    case ("--width")
       read(val, *, iostat=ios) cfg%width
       apply_option = (ios == 0)
    case ("--height")
       read(val, *, iostat=ios) cfg%height
       apply_option = (ios == 0)
    case ("--type")
       if (trim(val) == "mandelbrot") then
          cfg%fractal_type = TYPE_MANDELBROT
       else if (trim(val) == "julia") then
          cfg%fractal_type = TYPE_JULIA
       else if (trim(val) == "ship") then
          cfg%fractal_type = TYPE_BURNINGSHIP
       else if (trim(val) == "tricorn") then
          cfg%fractal_type = TYPE_TRICORN
       else if (trim(val) == "multibrot") then
          cfg%fractal_type = TYPE_MULTIBROT
       else if (trim(val) == "celtic") then
          cfg%fractal_type = TYPE_CELTIC
       else if (trim(val) == "perpendicular") then
          cfg%fractal_type = TYPE_PERPENDICULAR
       else
          apply_option = .false.
       end if
    case ("--power")
       read(val, *, iostat=ios) cfg%power
       apply_option = (ios == 0)
    case ("--freq")
       read(val, *, iostat=ios) cfg%cycle_freq
       apply_option = (ios == 0)
    case ("--frames")
       read(val, *, iostat=ios) cfg%frames
       apply_option = (ios == 0)
    case ("--zoom-start")
       read(val, *, iostat=ios) cfg%zoom_start
       apply_option = (ios == 0)
    case ("--zoom-end")
       read(val, *, iostat=ios) cfg%zoom_end
       apply_option = (ios == 0)
    case ("--output-dir")
       cfg%output_dir = trim(val)
    case ("--iter")
       read(val, *, iostat=ios) cfg%max_iter
       apply_option = (ios == 0)
    case ("--output")
       cfg%output = trim(val)
    case ("--palette")
       cfg%palette = adjustl(val)
    case ("--progress-every")
       read(val, *, iostat=ios) cfg%progress_every
       apply_option = (ios == 0)
    case ("--threads")
       read(val, *, iostat=ios) cfg%threads
       apply_option = (ios == 0)
    case ("--julia-cx")
       read(val, *, iostat=ios) cfg%julia_cx
       apply_option = (ios == 0)
    case ("--julia-cy")
       read(val, *, iostat=ios) cfg%julia_cy
       apply_option = (ios == 0)
    case ("--xmin")
       read(val, *, iostat=ios) cfg%x_min
       if (ios == 0) cfg%bounds_provided = .true.
       apply_option = (ios == 0)
    case ("--xmax")
       read(val, *, iostat=ios) cfg%x_max
       if (ios == 0) cfg%bounds_provided = .true.
       apply_option = (ios == 0)
    case ("--ymin")
       read(val, *, iostat=ios) cfg%y_min
       if (ios == 0) cfg%bounds_provided = .true.
       apply_option = (ios == 0)
    case ("--ymax")
       read(val, *, iostat=ios) cfg%y_max
       if (ios == 0) cfg%bounds_provided = .true.
       apply_option = (ios == 0)
    case ("--center-x")
       read(val, *, iostat=ios) cfg%center_x
       apply_option = (ios == 0)
    case ("--center-y")
       read(val, *, iostat=ios) cfg%center_y
       apply_option = (ios == 0)
    case ("--zoom")
       read(val, *, iostat=ios) cfg%zoom
       apply_option = (ios == 0)
    case default
       apply_option = .false.
    end select
  end function apply_option

end module mod_cli
