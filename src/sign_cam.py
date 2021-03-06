# 표지판 classifier
# 현지웅, 김성우


import threading
import time
import cv2
import numpy as np
import tensorflow as tf

# ==========================================
from src.shape_detection import shape_detect


class SignCam:
    def __init__(self):
        self.sign_trigger = 0
        self.is_in_mission = False
        self.sign = [[0 for col in range(7)] for row in range(2)]

        # [for test] './TestVideos/sign_cut.mp4'
        # [for real time data] 2
        self.cam = cv2.VideoCapture(2)

        self.cam.set(3, 800)
        self.cam.set(4, 448)
        self.sign2action = "Nothing"
        self.mission_number = 0
        self.done = 0

        self.thread = threading.Thread(target=self.detect_one_frame)
        self.stop_fg = False
        self.exit_fg = False

        self.sign_init()

    # modes = {'DEFAULT': 0, 'PARKING': 1, 'STATIC_OBS': 2,  'MOVING_OBS': 3,
    #           'S_CURVE': 4, 'NARROW': 5, 'U_TURN': 6, 'CROSS_WALK': 7}

    def sign_control(self):
        return self.sign_trigger

    def start(self):
        self.thread.start()

    def restart(self):
        self.stop_fg = False

    def stop(self):
        self.stop_fg = True

    def exit(self):
        self.exit_fg = True

    def sign_init(self):
        self.sign[0][0] = 'Bicycles'  # MOVING_OBS 3
        self.sign[0][1] = 'Crosswalk_PedestrainCrossing'  # CROSS_WALK 7
        self.sign[0][2] = 'Double_bend'  # S_Curve 4
        self.sign[0][3] = 'Narrow_Carriageway'  # NARROW 5
        self.sign[0][4] = 'Parking_Lot'  # PARKING 1
        self.sign[0][5] = 'Roadworks'  # STATIC_OBS 2
        self.sign[0][6] = 'u_turn'  # U_TURN 6
        self.sign[1][0] = 0
        self.sign[1][1] = 0
        self.sign[1][2] = 0
        self.sign[1][3] = 0
        self.sign[1][4] = 0
        self.sign[1][5] = 0
        self.sign[1][6] = 0

    def sign_reinit(self):
        self.sign[1][0] = 0
        self.sign[1][1] = 0
        self.sign[1][2] = 0
        self.sign[1][3] = 0
        self.sign[1][4] = 0
        self.sign[1][5] = 0
        self.sign[1][6] = 0

    def countup_recognition(self, result_sign, prob):
        for i in range(7):
            if self.sign[0][i] == result_sign and (prob > 0.95):  # 확률 95퍼 이상, 조정 시 값만 바꿔주세요.
                self.sign[1][i] = self.sign[1][i] + 1
                break

    def print_sign(self):  # test code 에서 사용될 출력 함수
        for i in range(7):
            print("print_sign: ", self.sign[0][i], self.sign[1][i])

    def set_sign2action(self):
        # 만약 한 표지판의 인식 횟수가 일정 이상이 되면, 그 sign에 대한 action을 준비하고, 횟수 모두 초기화하기 (3번도 다양하게 바꿀 수 있음)
        for i in range(7):
            print("count:", i, self.sign[1][i])
            if self.sign[1][i] >= 1:  # 횟수 트리거
                self.sign2action = self.sign[0][i]
                self.sign[1][0] = 0
                self.sign[1][1] = 0
                self.sign[1][2] = 0
                self.sign[1][3] = 0
                self.sign[1][4] = 0
                self.sign[1][5] = 0
                self.sign[1][6] = 0
                break

    def detect_one_frame(self):
        while True:

            if self.exit_fg is True: break
            if self.stop_fg is True: time.sleep(1); continue
            ############################################################
            time.sleep(0.1)
            frame_okay, frame = self.cam.read()  # 한 프레임을 가져오자.

            img_list = shape_detect(frame)  # 이미지 중 표지판이 있는 곳 확인

            # 제어에 넘겨주는 연산 여부 (속도를 줄이는 트리거)
            if len(img_list) == 0:
                self.sign_trigger = 0
            else:
                self.sign_trigger = 1

            cv2.imshow('1', frame)

            if cv2.waitKey(1) & 0xff == 27:
                return

            # 표지판이 있는 곳의 이미지에 대하여
            if len(img_list) > 0:
                result_sign, prob = self.process_one_frame_sign(img_list[0])  # 그 이미지가 어떤 표지판인지 확인한다
                print(">>>>result sign:", result_sign, "/ score:", prob)
                self.countup_recognition(result_sign, prob)  # 확률이 높으면 그 표지판을 한 번 인식했다고 기록
                self.set_sign2action()
                img_list.clear()

    def get_mission(self):
        # modes = {'DEFAULT': 0, 'PARKING': 1, 'STATIC_OBS': 2,  'MOVING_OBS': 3,
        #           'S_CURVE': 4, 'NARROW': 5, 'U_TURN': 6, 'CROSS_WALK': 7}
        if self.sign2action == "Nothing":
            self.mission_number = 0
        elif self.sign2action == 'Parking_Lot':
            self.mission_number = 1
        elif self.sign2action == 'Roadworks':
            self.mission_number = 2
        elif self.sign2action == 'Bicycles':
            self.mission_number = 3
        elif self.sign2action == 'Double_bend':
            self.mission_number = 4
        elif self.sign2action == 'Narrow_Carriageway':
            self.mission_number = 5
        elif self.sign2action == 'u_turn':
            self.mission_number = 6
        elif self.sign2action == 'Crosswalk_PedestrainCrossing':
            self.mission_number = 7

        if self.mission_number > 0:
            self.sign_reinit()

        self.sign2action = "Nothing"
        print("mission_number>>>> ", self.mission_number)
        return self.mission_number

    def is_in_this_mission(self, ndarray):
        try:
            if np.sum(ndarray) >= 1:
                return True
            else:
                return False
        except Exception as e:
            return False

    def process_one_frame_sign(self, frame):
        if len(frame) < 1:
            return "Nothing", 0.00

        # 프레임 시작 시간 측정
        t1 = time.time()

        cv2.imwrite('test.jpg', frame)

        image_data = tf.gfile.FastGFile('test.jpg', 'rb').read()

        # label_lines = [line.rstrip() for line in tf.gfile.GFile('')]
        label_lines = ['Bicycles', 'Crosswalk_PedestrainCrossing', 'Double_bend', 'Narrow_Carriageway', 'Parking_Lot',
                       'Roadworks', 'u_turn']

        if self.done == 0:
            with tf.gfile.FastGFile(
                    "../rsc/DeepLearning/minimal_graph.proto", 'rb') as f:
                # with tf.device('/gpu:0'):
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                _ = tf.import_graph_def(graph_def, name='')
            self.done = self.done + 1

        # config=tf.ConfigProto(log_device_placement=True)

        with tf.Session() as sess:
            # Feed the image_data as input to the graph and get first prediction
            # Feed data tensor 이름 각각 입력 (softmax_tensor가 y_eval, predictions가 x 데이터인듯)
            softmax_tensor = sess.graph.get_tensor_by_name('InceptionV1/Logits/Predictions/Softmax:0')
            predictions = sess.run(softmax_tensor, {'input_image:0': image_data})
            # Sort to show labels of first prediction in order of confidence
            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
            # print(top_k)

            print()
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                print('%s (score = %.5f)' % (human_string, score))

        t2 = time.time()

        print("one frame time: ", t2 - t1)

        # 가장 높은 확률인 표지판 이름과 확률을 return해줌으로서 count를 할 수 있도록 함.
        return label_lines[top_k[0]], predictions[0][top_k[0]]


if __name__ == "__main__":
    import os

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    current_signcam = SignCam()
    current_signcam.start()
