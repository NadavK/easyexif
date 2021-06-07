from datetime import datetime
from datetime import timedelta
import exiftool         # pip install PyExifTool
import glob
import os
import piexif           # pip install piexif
import pywintypes       # pip install pywin32
import re
import sys
import traceback
import warnings
import win32con
import win32file        # pip install pywin32


et = None       # instance of ExifTool for video files

filename_delimiter = '~'

jpg_exif_tags = [
        ['0th', 0x0132],        # "DateTime" ExifTool="EXIF:ModifyDate"
        ['Exif', 0x9003],       # "DateTimeOriginal" ExifTool="EXIF:DateTimeOriginal" 
        ['Exif', 0x9004],       # "DateTimeDigitized" ExifTool="EXIF:CreateDate"
    ]

exif_tags_video_fetch = [
    'EXIF:ModifyDate', 'XMP:ModifyDate', 'QuickTime:ModifyDate', 
    'EXIF:DateTimeOriginal', 'XMP:DateTimeOriginal',
    'EXIF:CreateDate', 'XMP:CreateDate', 'QuickTime:CreateDate', 
    'EXIF:EncodingTime', 'XMP:EncodingTime', 'QuickTime:EncodingTime', 
    ]

exif_tags_video_search = [                 # for some reason exiftool sometimes returns without the group name
    'EXIF:ModifyDate', 'XMP:ModifyDate', 'ModifyDate', 
    'EXIF:DateTimeOriginal', 'XMP:DateTimeOriginal', 'DateTimeOriginal',
    'EXIF:CreateDate', 'XMP:CreateDate', 'CreateDate',
    ]

def getExifTool():
    global et
    if not et:
        # '-charset cp437'
        # Try to execute ExifTool in this script's path
        path_to_exitftool = os.path.dirname(os.path.realpath(__file__)) + '\exiftool.exe'   # Check if exiftool is in the same directory as the script
        if not os.path.isfile(path_to_exitftool):   # Maybe it exists somewhere in the PATH?
            path_to_exitftool = 'exiftool.exe'
        try:
            et = exiftool.ExifTool(common_args=['-preserve','-overwrite_original'], executable_=path_to_exitftool)
            et.start()
        except Exception as e:
            et = None
            traceback.print_exc()
            print()
            print()
            print('**********************************************************************')
            print('***  ExifTool required, download from here: https://exiftool.org/  ***')
            print('***  Make sure ExifTool is somewhere in the PATH.                  ***')
            print('**********************************************************************')
            print()
            print()
            exit()
    return et


def clearExifTool():
    global et
    if et:
        et.terminate()
        et = None


def getFileDates(filepath):        
    return (datetime.fromtimestamp(os.path.getctime(filepath)),
             datetime.fromtimestamp(os.path.getmtime(filepath)),
             datetime.fromtimestamp(os.path.getatime(filepath)))

def setFileDates(filepath, ctime = None, mtime = None, atime = None):
    import time
    # https://stackoverflow.com/questions/4996405/how-do-i-change-the-file-creation-date-of-a-windows-file
    try:
        currentTimes = getFileDates(filepath)
        
        if ctime is None:
            ctime = currentTimes[0]
        if mtime is None:
            mtime = currentTimes[1]
        if atime is None:
            atime = currentTimes[2]

        # adjust for day light savings
        now = time.localtime()
        #ctime += 3600 * (now.tm_isdst - time.localtime(ctime).tm_isdst)
        #mtime += 3600 * (now.tm_isdst - time.localtime(mtime).tm_isdst)
        #atime += 3600 * (now.tm_isdst - time.localtime(atime).tm_isdst)


        # change time stamps
        winfile = win32file.CreateFile(
            filepath, win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None, win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL, None)
        #print('3', mtime)
        with warnings.catch_warnings():
            try:
                warnings.simplefilter("ignore")
                win32file.SetFileTime(winfile, \
                    pywintypes.Time(time.mktime(ctime.timetuple())), \
                    pywintypes.Time(time.mktime(atime.timetuple())), \
                    pywintypes.Time(time.mktime(mtime.timetuple())))          # If this fails, consider just setting modified time using built-in python function. Or reduce float to int.
            except:
                print('Using alternate file time setting')
                os.utime(filepath, (atime.timestamp(), mtime.timestamp()))
        winfile.close()
        return True
    except Exception as e:
        traceback.print_exc()

    return False


def getExifDateJpeg(filename):
    exif_dict = piexif.load(filename)

    exif_date = None

    for tag in jpg_exif_tags:
        try:
            exif_date = exif_dict[tag[0]][tag[1]].decode('ascii')  #0123:56:89 12:45:78
            #print('exif_date', exif_date)
            return datetime(year=int(exif_date[0:4]), month=int(exif_date[5:7]), day=int(exif_date[8:10]), hour=int(exif_date[11:13]), minute=int(exif_date[14:16]), second=int(exif_date[17:20]))
        except:
            pass

    print('No dates found in Exif')
    return False


def getExifDateVideo(filename):
    et = getExifTool()
    if not et:
        return False

    exif_date = None
    exif_dict = et.get_tags(exif_tags_video_fetch, filename)
    #exif_dict = et.get_metadata(filename)  # all tags
    print(exif_dict)
    for tag in exif_tags_video_search:
        try:
            exif_date = exif_dict[tag]
            print(tag, exif_date)
            try:
                # Try Exif long-date format: 2000:01:01 01:01:01+02:00
                iso_date = '{0}-{1}-{2}'.format(exif_date[0:4],exif_date[5:7],exif_date[8:])
                #print(iso_date)
                return datetime.fromisoformat(iso_date)
            except: pass
            #print('exif_date:', exif_date)
            return datetime(year=int(exif_date[0:4]), month=int(exif_date[5:7]), day=int(exif_date[8:10]), hour=int(exif_date[11:13]), minute=int(exif_date[14:16]), second=int(exif_date[17:20]))
        except:
            pass
        
    print('No dates found in Exif')
    return False
 

def setExifDateVideo(filename, newdate):
    et = getExifTool()
    if not et:
        return False

    d = '{0:%Y:%m:%d %H:%M:%S}'.format(newdate)
    tags = {'AllDates': '{0}'.format(d)}

    # Check if file has EncodingTime, because we only want to set it if it already exists
    exif_dict = et.get_tags(exif_tags_video_fetch, filename)
    print(exif_dict)
    if 'EncodingTime' in exif_dict.keys():
        print('Has encoding time tag')
        tags['EncodingTime'] = d
    
    #x = et.set_tags('-P -AllDates="{0:%Y:%m:%d %H:%M:%S}" "{1}"'.format(newdate, filename))
    result = et.set_tags(tags, filename)
    if b'1 image files updated\r\n' in result:
        return True
    print("exiftool FAILED:", result.decode('ascii'))


def setExifDateJpeg(filename, newdate):
    rc = True
    datestr = newdate.strftime('%Y:%m:%d %H:%M:%S').encode('ascii')

    try:
        exif_dict = piexif.load(filename)
        
        # Change all dates
        for ifd_name, ifd_dict in exif_dict.items():
            if ifd_name != 'thumbnail':
                for key, value in ifd_dict.items():
                    #if key==0x9004:    # Don't overwrite 'digitized'
                    #    continue
                    try:
                        string = value.decode('ascii')
                        if re.search(r'\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}', string):
                            #print('{0} IDF #{1} 0x{1:02X}: {2}'.format(ifd_name, key, string))
                            exif_dict[ifd_name][key] = datestr
                        #    #print(key, value[:10])
                        #    print(key, value.decode('ascii'))
                    except Exception as e:
                        pass
                        #print(ifd_name, key, value)
                        #traceback.print_exc()
                        #rc = False

        # Explicitly set these date tags
        for tag in jpg_exif_tags:
            exif_dict[tag[0]][tag[1]] = datestr

        #exif_dict['0th'][0x0132] =  '2001:01:11 11:11:11'.encode('ascii')      # "DateTime" ExifTool="EXIF:ModifyDate"
        #exif_dict['Exif'][0x9003] = '2002:02:12 12:12:12'.encode('ascii')      # "DateTimeOriginal" ExifTool="EXIF:DateTimeOriginal"
        #exif_dict['Exif'][0x9004] = '2003:03:13 13:13:13'.encode('ascii')      # "DateTimeDigitized" ExifTool="EXIF:CreateDate"

        # Save
        piexif.insert(piexif.dump(exif_dict), filename)
        return rc
    except Exception as e:
        traceback.print_exc()
        return False


def isFileJpeg(filename):
    file_extension = os.path.splitext(filename)[1]
    return file_extension.lower() in ['.jpg', '.jpeg']


def getExifDate(filename):
    if isFileJpeg(filename):
        return getExifDateJpeg(filename)
    else:
        return getExifDateVideo(filename)


def setExifDates(filename, newdate):
    if isFileJpeg(filename):
        return setExifDateJpeg(filename, newdate)
    else:
        return setExifDateVideo(filename, newdate)


def calculateDateTime(new, old):
    if new[0] in ['+', '-']:
        hours, minutes, seconds, *rest = (new[1:]+':0:0').split(':')     # next line will deal with defaults
        delta = timedelta(hours=(int(hours) or 0), minutes=(int(minutes) or 0), seconds=(int(seconds) or 0))
        if new[0] == '+':
            dt = old + delta
        else:
            dt = old - delta
    else:
        dt = datetime.fromisoformat(new)
        if len(new)<=10:           # Just date. So use original time
            dt = datetime.combine(dt.date(), old.time()) #, tzinfo=self.tzinfo)

    #print('4', dt)
    return dt


def handleFile(target, source, filename):
    rc = True
    originalfilename = filename
    originalfilenamePath, originalfilenameOnly = os.path.split(filename)
    # if not isFileJpeg(filename):
    #     try:
    #         fn = filename.encode('ascii')   # Exiftool doesn't handle non-ascii filename
    #     except:
    #         filename = 'filetimestemp-' + datetime.now().strftime("%Y%m%d-%H%M%S")
    #         os.rename(originalfilename, filename)
        
    ctime, mtime, atime = getFileDates(filename)   # If changing Exif data, we will need to rewrite the previous modified date
    
    new_date = None
    if source == 'm' or source == '-m':
        new_date = mtime
    elif source == 'x' or source == '-x':
        new_date = getExifDate(filename)
        if not new_date:
            print('Exif date not found', originalfilename)
            return False
    elif source == 'n' or source == '-n':
        try:
            #if originalfilenameOnly.find(filename_delimiter) == -1:
            #    print('date not found in filename: ', originalfilename)
            #    return False
            #new_date = originalfilenameOnly.split(filename_delimiter)[0]
            #new_date = '{0}-{1}-{2} {3}:{4}:{5}'.format(new_date[0:4],new_date[4:6],new_date[6:8],new_date[9:11],new_date[11:13],new_date[13:15])
            #new_date = datetime.fromisoformat(new_date)
            
            filenameNoExt = os.path.splitext(originalfilenameOnly)[0]
            # Format: YYYYMMDD?HHMMSS
            if filenameNoExt[8].isdigit() or (len(filenameNoExt)>15 and filenameNoExt[15].isdigit()): #if the char at the end of the date is also a digit, then this is not a date
                raise
            new_date = datetime(year=int(filenameNoExt[0:4]), month=int(filenameNoExt[4:6]), day=int(filenameNoExt[6:8]), hour=int(filenameNoExt[9:11]), minute=int(filenameNoExt[11:13]), second=int(filenameNoExt[13:15]))
        except:
            try:
                # Format: YYYY?MM?DD?HH?MM?SS
                if (filenameNoExt[4].isdigit() or filenameNoExt[7].isdigit() or filenameNoExt[10].isdigit() or filenameNoExt[13].isdigit() or filenameNoExt[16].isdigit()) \
                 or len(filenameNoExt)>19 and filenameNoExt[19].isdigit():    #if the char at the end of the date is also a digit, then this is not a date
                    raise
                new_date = datetime(year=int(filenameNoExt[0:4]), month=int(filenameNoExt[5:7]), day=int(filenameNoExt[8:10]), hour=int(filenameNoExt[11:13]), minute=int(filenameNoExt[14:16]), second=int(filenameNoExt[17:20]))
            except:
                print('Date not found in filename: ', originalfilename)
                return False
    else:   # source is expected to be a date
        new_date = calculateDateTime(source, mtime)     # use modified time if only date was supplied

    if 'x' in target:
        if not setExifDates(filename, new_date):
            rc = False
    
    set_file_date = False
    if 'c' in target:
        ctime = set_file_date = new_date
    if 'm' in target:
        mtime = set_file_date = new_date
    if 'a' in target:
        atime = set_file_date = new_date
    if set_file_date or 'x' in target:  # if we saved exif data, we need to reset the file system dates
        if not setFileDates(filename, ctime, mtime, atime):
            rc = False

    if 'n' in target:
        oldfilenameOnly = originalfilenameOnly.split(filename_delimiter, 1)[-1]        # -1 returns the last part of the split. If no split, returns the whole string.
        newfilename = os.path.join(originalfilenamePath, new_date.strftime("%Y%m%d-%H%M%S") + filename_delimiter + oldfilenameOnly)
        os.rename(filename, newfilename)
        if originalfilenameOnly != newfilename:
            print('Renamed {0} > {1}'.format(originalfilename, newfilename))

    return rc


def main(target, source, pathname):
    rc = True
    i = 0
    for filename in glob.glob(pathname):
        i = i + 1
        if not handleFile(target, source, filename):
            rc = False
    print('{0} file{1} {2} {3}'.format('No' if i==0 else i, 's' if i!=1 else '', 'found to process.' if i==0 else 'processed', 'succesfully.' if i and rc else 'with FAILURES!!!' if i else ''))


if __name__ == "__main__":
    try:
        target = sys.argv[1]
        source = sys.argv[2]
        file = sys.argv[3]
        main(target, source, file)

    except Exception:
        traceback.print_exc()
        print()
        print('Target(s)-to-set source-values-from path')
        print('Target(s): -cmax')
        print('Source: take from m/x or YYYY-MM-DD[THH[:MM[:SS]] or [+HH:MM[:SS]]]')
        print('-c Set Creation date')
        print('-m Set Modified date')
        print('-a Set Access date')
        print('-x Set Exif dates')
        print('-n Prefix filename with date. NOTE: will remove previous file date if exists.')
        print('-0 Just print to screen.')
        print('Relative dates in format +HH[[:MM]:SS] or -HH[[:MM]:SS]')
    finally:
        clearExifTool()
