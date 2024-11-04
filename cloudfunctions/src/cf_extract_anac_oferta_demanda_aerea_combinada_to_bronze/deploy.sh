#!/bin/bash

gcloud alpha functions deploy $FUNCTION_NAME \
  --gen2 \
  --project $PROJECT \
  --region $REGION \
  --source $SOURCE \
  --runtime $RUNTIME \
  --entry-point $ENTRY_POINT \
  --trigger-http \
  --no-allow-unauthenticated \
  --cpu $CPU \
  --memory $MEMORY \
  --timeout $TIMEOUT \
  --concurrency $CONCURRENCY \
  --service-account $SERVICE_ACCOUNT \
  --set-secrets="$SET_SECRETS" \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --set-env-vars="$ENV_VARS"