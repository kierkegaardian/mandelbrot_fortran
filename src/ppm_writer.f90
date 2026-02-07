module mod_ppm_writer
  use, intrinsic :: iso_fortran_env, only: int8, int32, error_unit
  implicit none
  private
  public :: write_ppm

contains

  subroutine write_ppm(filename, width, height, data)
    character(len=*), intent(in) :: filename
    integer, intent(in) :: width, height
    integer(int32), intent(in) :: data(3, width, height)
    
    integer :: unit_num, iostatus

    open(newunit=unit_num, file=filename, status='replace', &
         access='stream', action='write', iostat=iostatus)
    
    if (iostatus /= 0) then
       write(error_unit, '(A,1X,A,1X,I0)') "Error: Could not open file", trim(filename), iostatus
       return
    end if

    ! Write PPM header (P6). Canonical format is three ASCII lines.
    write(unit_num) "P6" // char(10)
    call write_ascii_line(unit_num, width, height)
    write(unit_num) "255" // char(10)

    ! Write the binary data
    ! Fortran stores arrays in column-major order (width then height)
    ! But PPM expects row-major (scanning rows).
    ! We need to transpose logic or write appropriately.
    ! Our data array is (rgb, x, y).
    ! We need to write: for y=1..h, for x=1..w, write r,g,b
    
    call write_pixels(unit_num, width, height, data)

    close(unit_num)
  end subroutine write_ppm

  subroutine write_pixels(u, w, h, d)
    integer, intent(in) :: u, w, h
    integer(int32), intent(in) :: d(3, w, h)
    integer :: x, y
    integer(int8) :: pixel(3) ! Byte array for RGB

    do y = 1, h
       do x = 1, w
          pixel(1) = to_int8_byte(d(1, x, y))
          pixel(2) = to_int8_byte(d(2, x, y))
          pixel(3) = to_int8_byte(d(3, x, y))
          write(u) pixel
       end do
    end do
  end subroutine write_pixels

  subroutine write_ascii_line(u, w, h)
    integer, intent(in) :: u, w, h
    character(len=64) :: line
    write(line, '(I0, 1X, I0)') w, h
    write(u) trim(line) // char(10)
  end subroutine write_ascii_line

  pure integer(int8) function to_int8_byte(v) result(b)
    integer(int32), intent(in) :: v
    integer(int32) :: t
    t = modulo(v, 256_int32)
    if (t > 127_int32) then
       b = int(t - 256_int32, int8)
    else
       b = int(t, int8)
    end if
  end function to_int8_byte

end module mod_ppm_writer
