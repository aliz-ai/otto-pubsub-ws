```shell script
gcloud config set project edgar-prunk-eger-sandbox

export PROJECT=$(gcloud config list project --format "value(core.project)")
export PROJECTNUMBER=673415893162
export INPUT_BUCKET_NAME=otto-pubsub-ws-input
export INVOKER_SERVICE_ACCOUNT=otto-cloud-run-pubsub-invoker
```

```shell script
gcloud config set run/region europe-west1
```

```shell script
gsutil mb gs://otto-pubsub-ws-input
```

```shell script
gcloud pubsub topics create ottoNotificationTopic
```

Create Object change notifications to our Pub/Sub topic: 

```shell script
gsutil notification create -t ottoNotificationTopic -f json gs://$INPUT_BUCKET_NAME
```

```shell script
gcloud builds submit --tag gcr.io/$PROJECT/otto-pubsub

gcloud run deploy otto-pubsub-demo \
    --platform managed \
    --image gcr.io/$PROJECT/otto-pubsub \
    --memory=1G 
```

Save service url, we will need it later:
```shell script
export RUN_SERVICE_URL='https://otto-pubsub-demo-oa3moqyyda-ew.a.run.app/'
```

## Integrating with Pub/Sub

Now that we have deployed our Cloud Run service, we will configure Pub/Sub to push messages to it.

To integrate the service with Pub/Sub:

### 1. Enable Pub/Sub to create authentication tokens in your project:

```shell script
gcloud projects add-iam-policy-binding $PROJECT \
     --member=serviceAccount:service-$PROJECTNUMBER@gcp-sa-pubsub.iam.gserviceaccount.com \
     --role=roles/iam.serviceAccountTokenCreator
```

### 2. Create or select a service account to represent the Pub/Sub subscription identity.

```shell script
gcloud iam service-accounts create $INVOKER_SERVICE_ACCOUNT \
     --display-name "OTTO Cloud Run Pub/Sub Invoker"
```

### 3. Create a Pub/Sub subscription with the service account

```shell script
gcloud run services add-iam-policy-binding otto-pubsub-demo \
    --member=serviceAccount:otto-cloud-run-pubsub-invoker@$PROJECT.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --platform managed
```


```shell script
gcloud pubsub subscriptions create ottoNotificationSubscription --topic ottoNotificationTopic \
   --push-endpoint=$RUN_SERVICE_URL \
   --push-auth-service-account=$INVOKER_SERVICE_ACCOUNT@$PROJECT.iam.gserviceaccount.com
```

## Create Pub/Sub topic and subscription for predictions

```shell script
gcloud pubsub topics create ottoPredictionTopic
```
