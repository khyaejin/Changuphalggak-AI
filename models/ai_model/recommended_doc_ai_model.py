import joblib

# AI 모델 로드
def load_model():
    # TODO: 해당 model을 생성하는 부분이 제일 핵심적인 부분
    # TODO: Colab에서 학습 진행한 후 완성된 모델 파일을 프로젝트에 복사해 사용할 예정
    model = joblib.load("path_to_your_model_file.pkl")  # 실제 모델 파일 경로 지정. 깃에 올라갈 수 있는 크기인 경우 깃에서 관리 예정
    return model

# AI 모델을 사용하여 추천 사업 목록 반환
def get_recommended_documents_from_ai(model, data):
    prediction = model.predict([data])  # request로 준 데이터를 모델에 넣고 예측 결과 반환
    return prediction
