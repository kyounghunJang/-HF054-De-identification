# [HF054]비정형개인정보 비식별처리 기술 개발
- 프로젝트 KPT회고 링크: https://codingjang.tistory.com/71
- 시연 연상 링크: https://youtu.be/Jj0mzE0zwUs?si=KUZ0fTTik4aA1HT3
---
## 프로젝트 소개 
 의료데이터의 분석 및 활용이 서비스 품질 발전에 큰 기여를 할 수 있는 상황이다. 하지만 이를 활용하기 위해서는 의료데이터에 포함된 개인정보를 제거해야한다. 따라서 비정형 데이터에서 개인정보를 추출 및 제거하는 기술을 개발하고 이를 활용한 자동화 파이프라인을 구축해보려고 한다.

## 적용기술 및 아키텍처
- 비식별 처리 : 데이터 마스킹, 데이터 삭제 기술을 사용하여 민감한 개인정보를 비식별처리
- 비식별 처리 자동화 파이프라인 : 병원 서버를 S3로 가정하고 데이터가 업로드 되면 배치처리로 비식별처리 후 완료된 데이터를 DB에 저장하는 파이프라인
- EasyOCR : 이미지 속 텍스트를 판별하여 추출하는 기술
- 모니터링 : 파이프라인 작동시 성공적으로 비식별 처리가 완료되었는지 확인 (SSM 로그를 확인)


### 개발 환경
![개발환경 이미지](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2F48brG%2Fbtsz1ulvJBC%2FXkYpKPv9tjPSbjXcw4Sj60%2Fimg.png)

### 아키텍처 
![아키텍처 이미지](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fej3sy2%2FbtszXFPkNW2%2F9uDe5IKBSziOKE0aiwY7v0%2Fimg.png)

## 주요기능
- 텍스트 검출/ 추출 및 전처리 : EasyOcr을 사용하여 텍스트를 검출 및 추출 후 모델에 적합한 데이터로 전처리
- 비식별 처리 : SparkML의 Gradient Boosting Tree을 사용하여 데이터 비식별 처리
- 비식별처리 자동화 : 업로드 -> SQS -> Lambda -> SSM(Run Shell script) -> EC2->DB or Flask 의 순서로 비식별처리 과정을 수행한다.
- 검색 웹 인터페이스 : Flask로 웹서버를 구축 데이터 사용자가 필요한 데이터의 부위를 검색 및 다운로드 가능
- DB : MySQL에 비식별 처리가 완료된 이미지 데이터의 이미지 URL을 저장

## 수행일정
![수행일정 이미지](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FclUgfB%2FbtszXKiKaOH%2FAtPKDwVSNOWJ4XwL4F0Nn1%2Fimg.png)
