# EasyExif

EasyExif is a Python library to easily edit EXIF dates in image and video files, and also file-system times (created/modified time).

## Installation
1. Make sure you have Python
1. Download [EasyExif](https://github.com/NadavK/easyexif/blob/main/easyexif.py)
1. Download Phil Harvey's amazing ExifTool: https://exiftool.org/
1. Install prerequisites:
```
pip install PyExifTool piexif pywin32
```

## Usage

```bash
python easyexif.py {to} {from} {filename}
```
{to} defines which attributes to update (can be multiple):
* <i>c</i>: OS Created-date
* <i>m</i>: OS modified-date
* <i>n</i>: Filename-prefix. Adds a prefix to the filename in this format: YYYYMMDD-HHMMSS~)
* <i>x</i>: EXIF

{from} defines where to take the value to be set:
* <i>c</i>: OS Created-date
* <i>m</i>: OS Modified-date
* <i>n</i>: Filename-prefix. Expects the filename to contain a date prefix in this format: YYYYMMDD-HHMMSS~)
* <i>x</i>: EXIF
* YYYY-MM-DD[<b><i>T</b></i>HH[:MM[:SS]]] explicit date
* +HH:MM[:SS] add time 
* -HH:MM[:SS] reduce time

{filename} can contain wildcards

##Examples
1. Set the modified-date from the exif-date:
    ```bash
    python easyexif.py m x *.jpg
    ```

1. Set the EXIF-date from the modified-date:
    ```bash
    python easyexif.py x m *.jpg

1. Set the EXIF-date and filename-prefix from the modified-date:
    ```bash
    python easyexif.py xn m *.jpg
    ```
    In addition to setting the exif-date, this will also prefix the modified-date to the filename using YYYYMMDD-HHMMSS~ format.<BR><BR>

1. Set the EXIF-date and modified-date from the filename:
    ```bash
    python easyexif.py xm n *.jpg
    ```
    Expects the filename to have a prefix of YYYYMMDD-HHMMSS~<BR><BR>

1. Set the EXIF-date and modified-date to the specified date:
    ```bash
    python easyexif.py xm 2022-01-01T01:02:03 *.jpg
    ```

1. Add time to the EXIF-date and modified-date:
    ```bash
    python easyexif.py xm +01:02:03 *.jpg

1. Reduce time from the EXIF-date and modified-date:
    ```bash
    python easyexif.py xm -01:02:03 *.jpg
    ```

## Caveats
* Only tested on Windows
* {filename} should be a file/files, but <i>not</i> a directory (otherwise it tries to apply changes to the directory itself).

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[GNU Affero General Public License v3.0](https://github.com/NadavK/easyexif/blob/main/LICENSE)
