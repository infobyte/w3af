import sys
import zlib

if __name__ == '__main__':
    filename = sys.argv[1]
    
    compressed_data = open(filename).read()[8:]
    uncompressed_data = zlib.decompress(compressed_data)
    
    output_file = '%s.bytecode' % filename
    open(output_file, 'w').write(uncompressed_data)
