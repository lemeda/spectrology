#!/usr/bin/env python

"""
Spectrology
This script is able to encode an image into audio file whose spectrogram represents input image.

License: MIT
Website: https://github.com/solusipse/spectrology
"""

import argparse
import array
import math
import sys
import timeit
import wave

from PIL import Image, ImageOps

# Logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG", format="%(asctime)s:%(name)s:%(lineno)s:%(levelname)s - %(message)s")


def convert(input_file, output, minfreq, maxfreq, pxs, wavrate, rotate, invert):
    img = Image.open(input_file).convert('L')

    # rotate image if requested
    if rotate:
        img = img.rotate(90)

    # invert image if requested
    if invert:
        img = ImageOps.invert(img)

    output = wave.open(output, 'wb')
    output.setparams((1, 2, wavrate, 0, 'NONE', 'not compressed'))

    freqrange = maxfreq - minfreq
    interval = freqrange / img.size[1]

    fpx = wavrate // pxs
    data = array.array('h')

    tm = timeit.default_timer()

    for x in range(img.size[0]):
        row = []
        for y in range(img.size[1]):
            yinv = img.size[1] - y - 1
            amp = img.getpixel((x, y))
            if amp > 0:
                row.append(genwave(yinv * interval + minfreq, amp, fpx, wavrate))

        for i in range(fpx):
            for j in row:
                try:
                    data[i + x * fpx] += j[i]
                except IndexError:
                    data.insert(i + x * fpx, j[i])
                except OverflowError:
                    if j[i] > 0:
                        data[i + x * fpx] = 32767
                    else:
                        data[i + x * fpx] = -32768

        logger.info("Conversion progress: %d%%   \r" % (float(x) / img.size[0] * 100))
        sys.stdout.flush()

    output.writeframes(data.tostring())
    output.close()

    tms = timeit.default_timer()

    print("Conversion progress: 100%")
    print("Success. Completed in %d seconds." % int(tms - tm))


def genwave(frequency, amplitude, samples, samplerate):
    cycles = samples * frequency / samplerate
    a = []
    for i in range(samples):
        x = math.sin(float(cycles) * 2 * math.pi * i / float(samples)) * float(amplitude)
        a.append(int(math.floor(x)))
    return a


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("INPUT", help="Name of the image to be convected.")
    parser.add_argument("-o", "--output", default="out.wav",
                        help="Name of the output wav file. Default value: out.wav).")
    parser.add_argument("-m", "--minfreq", default=200, help="Bottom frequency range. Default value: 200.", type=int)
    parser.add_argument("-M", "--maxfreq", default=20000, help="Top frequency range. Default value: 20000.", type=int)
    parser.add_argument("-p", "--pixels", default=30, help="Pixels per second. Default value: 30.", type=int)
    parser.add_argument("-s", "--sampling", default=44100, help="Sampling rate. Default value: 44100.", type=int)
    parser.add_argument("-r", "--rotate", default=False, help="Rotate image 90 degrees for waterfall spectrographs.",
                        action='store_true')
    parser.add_argument("-i", "--invert", default=False, help="Invert image colors.", action='store_true')
    args = parser.parse_args()

    logger.debug('Input file: %s.' % args.INPUT)
    logger.debug('Frequency range: %d - %d.' % (args.minfreq, args.maxfreq))
    logger.debug('Pixels per second: %d.' % args.pixels)
    logger.debug('Sampling rate: %d.' % args.sampling)
    logger.debug('Rotate Image: %s.' % ('yes' if args.rotate else 'no'))
    logger.debug('Invert colors: %s.' % ('yes' if args.invert else 'no'))

    convert(args.INPUT, args.output, args.minfreq, args.maxfreq, args.pixels, args.sampling, args.rotate, args.invert)


if __name__ == '__main__':
    main()
