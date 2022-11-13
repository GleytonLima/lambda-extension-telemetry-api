resource "null_resource" "install_python_dependencies" {
  provisioner "local-exec" {
    command = "bash ${path.module}/install_dependencies.sh"
  }
}

variable "SPLUNK_HOST" { type= string } 
variable "SPLUNK_HEC_TOKEN" { type= string } 
variable "SPLUNK_INDEX" { type= string } 

data "archive_file" "extension_zip" {
  type        = "zip"
  output_path = "${path.module}/extension_payload.zip"
  excludes    = []
  source_dir = "${path.module}/lambda-extensions"
  depends_on = [null_resource.install_python_dependencies]
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function_payload.zip"
  excludes    = []
  source_dir = "${path.module}/lambda-with-logs"
}

resource "aws_lambda_layer_version" "logs_api_layer" {
  filename   = "extension_payload.zip"
  layer_name = "lambda-layer-logs-api-extension"
  source_code_hash  = "${data.archive_file.extension_zip.output_base64sha256}"

  compatible_runtimes = ["python3.9"]
  depends_on = [
    data.archive_file.extension_zip,
  ]
}

resource "aws_iam_role" "iam_for_lambda" {

  name = "iam_for_lambda"

  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOF
}


resource "aws_lambda_function" "test_lambda" {
  filename      = "lambda_function_payload.zip"
  description   = "Lamba with extension"
  function_name = "lambda-with-logs"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "handler.handle"

  runtime = "python3.9"
  source_code_hash  = "${data.archive_file.lambda_zip.output_base64sha256}"

  layers = [aws_lambda_layer_version.logs_api_layer.arn]
  timeout = 10

  environment {
    variables = {
      SPLUNK_HOST = "${var.SPLUNK_HOST}",
      SPLUNK_HEC_TOKEN = "${var.SPLUNK_HEC_TOKEN}",
      SPLUNK_INDEX = "${var.SPLUNK_INDEX}",
      DISPATCH_MIN_BATCH_SIZE = 1
    }
  }

  depends_on = [
    data.archive_file.lambda_zip,
    aws_lambda_layer_version.logs_api_layer
  ]
}