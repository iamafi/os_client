// Client side C program to communicate with server and open GUI
#include <stdio.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <Python.h>
#include <sys/wait.h>


#define PORT 8080
#define JSON_MAX_SIZE 32768


char in_filename[] = "input.json", out_filename[] = "output.json"; 


void sigint_handler(int);
void unix_error(char *msg);
pid_t Fork(void);


int main(int argc, char *argv[])
{
    struct sockaddr_in server_sock;
    pid_t python_pid;
    char buffer[JSON_MAX_SIZE], *ip_address;
    int in_fd, out_fd, valread, sock = 0;
    long unsigned int py_argc = 2, in_filename_len = 11, out_filename_len = 12;
    
    wchar_t *py_argv[2];
    FILE* py_script_fp;
    const char * PY_SCRIPT_FILENAME = "main.py";

    // Read IP address and Port from command line argument
    if(argc < 2) {
        puts("You must pass IP address as the second string");
        return -1;
    }
    ip_address = argv[1];

    // Attach SIGINT handler
    signal(SIGINT, sigint_handler);

    // Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n Socket creation error \n");
        return -1;
    }
    puts("Created client socket");

    // Initialize server socket and connect to it
    memset(&server_sock, '0', sizeof(server_sock));
    server_sock.sin_family = AF_INET;
    server_sock.sin_port = htons(PORT);
    // Convert IPv4 and IPv6 addresses from text to binary form
    if (inet_pton(AF_INET, ip_address, &server_sock.sin_addr) <= 0) {
        printf("\nInvalid address / Address not supported \n");
        return -1;
    }
    if (connect(sock, (struct sockaddr *)&server_sock, sizeof(server_sock)) < 0) {
        printf("\nConnection Failed \n");
        return -1;
    }
    puts("Connection to the server established successfully");

    // Create fifos to communicate with python
    mkfifo(in_filename, 0666);
    mkfifo(out_filename, 0666);

    // Initialize python libraries for python use, open python script file
    Py_Initialize();
    py_script_fp = _Py_fopen(PY_SCRIPT_FILENAME, "r");

    // We are finally ready!
    printf("Ready for communication...\n");

    // Run python script in a separate thread
    if ((python_pid = Fork()) == 0) {
        py_argv[0] = Py_DecodeLocale(in_filename, &in_filename_len);
        py_argv[1] = Py_DecodeLocale(out_filename, &out_filename_len);
        PySys_SetArgv(py_argc, py_argv);
        PyRun_SimpleFile(py_script_fp, PY_SCRIPT_FILENAME);
        exit(0);
    }

    while (1) {
        // Receive output from python and send it to the server
        memset(buffer, 0, JSON_MAX_SIZE);
        in_fd = open(in_filename, O_RDONLY);
        valread = read(in_fd, buffer, JSON_MAX_SIZE - 1);
        close(in_fd);
        buffer[valread] = '\0';
        send(sock, buffer, valread, 0);

        // Receive response from server and send it to python
        memset(buffer, 0, JSON_MAX_SIZE);
        valread = read(sock, buffer, JSON_MAX_SIZE - 1);
        buffer[JSON_MAX_SIZE] = '\0';
        out_fd = open(out_filename, O_WRONLY);
        write(out_fd, buffer, valread);
        close(out_fd);
    }

    // Delete communication files
    unlink(in_filename);
    unlink(out_filename);

    // Kill python process
    kill(python_pid, SIGKILL);

    // Cleanup all data used by python script
    Py_Finalize();

    return 0;
}


void sigint_handler(int signum)
{
    // Delete communication files
    unlink(in_filename);
    unlink(out_filename);

    // Cleanup all data used by python script
    Py_Finalize();

    exit(0);
}


void unix_error(char *msg)
{
    fprintf(stderr, "%s : %s\n", msg, strerror(errno));
    exit(0);
}


pid_t Fork(void)
{
    pid_t pid;
    if ((pid = fork()) < 0)
        unix_error("Fork error");
    return pid;
}