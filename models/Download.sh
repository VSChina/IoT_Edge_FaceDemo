sudo apt-get update
sudo apt-get install -y curl
curl -o ./shape_predictor_68_face_landmarks.dat.bz2 'http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2'
bzip2 -d shape_predictor_68_face_landmarks.dat.bz2
cp ./shape_predictor_68_face_landmarks.dat ../src/azure/cloud_service/Detection_Module/
cp ./shape_predictor_68_face_landmarks.dat ../src/leaf/
unzip model-r34-arcface-ms1m-refine-v1.zip
cp -r ./model-r34-amf ../src/azure/cloud_service/Recognition_Module_CPU/insightface/models/
cp -r ./model-r34-amf ../src/azure/cloud_service/Recognition_Module_GPU/insightface/models/
