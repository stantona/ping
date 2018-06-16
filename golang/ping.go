package main

import (
	"fmt"
	"os"
	"syscall"
)

func calc_checksum(b []byte) uint16 {
	fmt.Println("=== calc_checksum ===")
	var total uint32

	// Calculate the value of each octet by doing a bitwise OR of each pair
	// of bytes.
	for i := 0; i < len(b); i += 2 {
		total += uint32(b[i])<<8 | uint32(b[i+1])
	}

	// While there are any overflowing bits, add them to the 16 bit mask of the value.
	for (total >> 16) > 0 {
		total = total>>16 + total&0xffff
	}

	// Return the two's complement
	return uint16(^total)
}

func main() {
	var err error
	var fd int

	icmp_identifier := os.Getpid() & 0xffff

	fd, err = syscall.Socket(syscall.AF_INET, syscall.SOCK_RAW, syscall.IPPROTO_ICMP)

	if err != nil {
		panic(err)
	}

	addr := syscall.SockaddrInet4{
		Port: 0,
		Addr: [4]byte{127, 0, 0, 1},
	}

	if err != nil {
		panic(err)
	}

	// Initial ICMP header (set all defaults for now)
	icmp := []byte{
		8, // ICMP Type (Ping)
		0, // ICMP Code
		0, // Checksum (16 bit)
		0,
		uint8(icmp_identifier >> 8), // Identifier (16 bit)
		uint8(icmp_identifier & 0xff),
		0, // Sequence (16 bit)
		0,
		0xC0, // Timestamp TODO: Put in a real timestamp
		0xDE,
	}
	checksum := calc_checksum(icmp)

	icmp[2] = byte(checksum >> 8)
	icmp[3] = byte(checksum)

	fmt.Println("CHECKSUM:", checksum)

	buffer := make([]byte, 256)
	err = syscall.Sendto(fd, icmp, 0, &addr)

	if err != nil {
		panic(err)
	}

	_, _, err = syscall.Recvfrom(fd, buffer, 0)

	if err != nil {
		panic(err)
	}

	fmt.Println("BUFFER:", buffer)

	defer syscall.Close(fd)
}
