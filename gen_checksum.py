import sys
import tait_cat as tait

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        print("Please provide message to checksum")
        sys.exit()


checksum = tait.calculate_checksum(message)

print(f"           Command: {message}")
print(f"          Checksum: {checksum}")
print(f"Command + Checksum: {message}{checksum}")