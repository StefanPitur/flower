from flwr.server import start_server


if __name__ == "__main__":
    start_server(
        server_address="localhost:56119",
        grpc_max_message_length=10
    )
    input("Press any key to stop the gRPC Server")
