import cv2
import math
import json
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()

parser.add_argument('--imagepath', '-i', type=str, required=True)
parser.add_argument('--annotationpath', '-a', type=str, required=True)
parser.add_argument('--imageoutput', '-m', type=str, required=True)
parser.add_argument('--annotationoutput', '-n', type=str, required=True)
parser.add_argument('--size', '-s', type=int, required=True)
parser.add_argument('--threshold', '-t', type=int, required=True)

args = parser.parse_args()

# 输入图片集路径
imagePath = args.imagepath
# 输入标签路径
annotationPath = args.annotationpath
# 图片输出路径
imageOutput = args.imageoutput
# 输出标签路径
annotationOutput = args.annotationoutput
# 切割图片的尺寸
size = args.size
# 丢弃图片的阈值
threshold = float(args.threshold) / 100

# 判断两个两个矩形是否重叠，返回矩形B在A的重叠部分，在B的比率
def is_over_lap(region, target):
    x1 = max(region['x1'], target['x1'])
    y1 = max(region['y1'], target['y1'])
    x2 = min(region['x2'], target['x2'])
    y2 = min(region['y2'], target['y2'])

    if (x1 < x2) and (y1 < y2):
        s = (target['x2'] - target['x1']) * (region['y2'] - region['y1'])
        return (x2 - x1) * (y2 - y1) / s
    else:
        return 0



def progress(imageInputPath, labelPath, size, threshold, imageOuput, annotationOutput):

    originImageName = os.path.split(imageInputPath)[-1].split('.')[0]

    # 读取标签labels文件
    f = open(labelPath, 'r')
    label_txt = f.readlines()[2:]
    f.close()

    # 以字典的形式存储labels
    label_detail = []
    for i in label_txt:
        temp_dict = {}
        i = i.split(' ')
        temp_dict['x1'] = float(i[0])
        temp_dict['y1'] = float(i[1])
        temp_dict['x2'] = float(i[4])
        temp_dict['y2'] = float(i[5])
        temp_dict['category'] = i[8]
        label_detail.append(temp_dict)

    # 读取图片
    img = cv2.imread(imageInputPath)

    # 图像的尺寸,第一个值是x是列，第二个是y是行
    sp = img.shape

    # 添加可能检测的目标
    subImg_dic = []
    x_max = sp[0]
    y_max = sp[1]
    # 按列分割

    startX = 0
    startY = 0

    counter = 0
    while startX + size < x_max:
        startY = 0
        while startY + size < y_max:
            subImg_dic.append({
                'x1': startX,
                'y1': startY,
                'x2': startX + size,
                'y2': startY + size,
                'name': str(counter),
                'yu': 0
            })
            counter += 1
            startY += int(size/2)
        subImg_dic.append({
            'x1': startX,
            'y1': y_max - 1 - size,
            'x2': startX + size,
            'y2': y_max - 1,
            'name': str(counter),
            'yu': 0
        })
        counter += 1
        startX += int(size/2)

    startY = 0
    while startY + size < y_max:
        subImg_dic.append({
            'x1': x_max - 1 - size,
            'y1': startY,
            'x2': x_max - 1,
            'y2': startY + size,
            'name': str(counter),
            'yu': 0
        })
        counter += 1
        startY += int(size / 2)

    subImg_dic.append({
        'x1': x_max - 1 - size,
        'y1': y_max - 1 - size,
        'x2': x_max - 1,
        'y2': y_max - 1,
        'name': str(counter),
        'yu': 0
    })

    # for i in range(0, math.ceil(sp[0] / size) * 2):
    #     # 按行分割
    #     for j in range(0, math.ceil(sp[1] / size) * 2):
    #         if ((i + 1) * size <= x_max) and ((j + 1) * size <= y_max):
    #             temp = {
    #                 'x1': i * size,
    #                 'y1': j * size,
    #                 'x2': (i + 1) * size,
    #                 'y2': (j + 1) * size,
    #                 'name': str(i + 1) + '_' + str(j + 1),
    #                 'yu': 0
    #             }
    #             subImg_dic.append(temp)
    #         if ((i + 1) * size <= x_max) and ((j + 1) * size > y_max):
    #             temp = {
    #                 'x1': i * size,
    #                 'y1': y_max - size,
    #                 'x2': (i + 1) * size,
    #                 'y2': y_max,
    #                 'name': str(i + 1) + '_' + str(j + 1),
    #                 'yu': 0
    #             }
    #             subImg_dic.append(temp)
    #         if ((i + 1) * size > x_max) and ((j + 1) * size <= y_max):
    #             temp = {
    #                 'x1': x_max - size,
    #                 'y1': j * size,
    #                 'x2': x_max,
    #                 'y2': (j + 1) * size,
    #                 'name': str(i + 1) + '_' + str(j + 1),
    #                 'yu': 0
    #             }
    #             subImg_dic.append(temp)
    #         if ((i + 1) * size > x_max) and ((j + 1) * size > y_max):
    #             temp = {
    #                 'x1': x_max - size,
    #                 'y1': y_max - size,
    #                 'x2': x_max,
    #                 'y2': y_max,
    #                 'name': str(i + 1) + '_' + str(j + 1),
    #                 'yu': 0
    #             }
    #             subImg_dic.append(temp)

    for region in subImg_dic:
        contained_targets = []

        for target in label_detail:
            if is_over_lap(region, target) > threshold:
                contained_targets.append({
                    'x1': target['x1'] - region['x1'],
                    'x2': min(target['x2'] - region['x1'], size-1),
                    'y1': target['y1'] - region['y1'],
                    'y2': min(target['y2'] - region['y1'], size-1),
                    'category': target['category']
                })
        if len(contained_targets) > 0:
           #with open(annotatuonOutput + region['name'] + '.txt', 'w+') as f:
           # if not os.path.exists(os.path.join(annotationOutput, originImageName + '/')):
           #     os.makedirs(os.path.join(annotationOutput, originImageName + '/'))
           # if not os.path.exists(os.path.join(imageOutput, originImageName+'/')):
           #     os.makedirs(os.path.join(imageOutput, originImageName+'/'))
           with open(os.path.join(annotationOutput, originImageName+'_'+region['name']+'.txt'), 'w+') as f:
                subImg = img[int(region['y1']):int(region['y2']), int(region['x1']):int(region['x2'])]
                output = subImg.copy()
                # 输出描述文件
                for contain in contained_targets:
                    f.write(json.dumps(contain) + '\n')
                # 绘制所有图中目标
                for target in contained_targets:
                    cv2.rectangle(output, (int(target['x1']), int(target['y1'])),
                                  (int(target['x2']), int(target['y2'])), (255, 0, 255), 5)
                cv2.imwrite(os.path.join(imageOutput, originImageName+'_'+region['name']+'.png'), output, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])


if __name__ == "__main__":
    for i in os.walk(imagePath):
        for imageName in i[2]:
            # 过滤掉不符合要求的文件
            if not imageName.startswith('P'):
                continue
            imageInputPath = os.path.join(imagePath, imageName)
            labelPath = os.path.join(annotationPath, imageName.split('.')[0] + '.txt')
            print(labelPath)
            print(imageInputPath)
            progress(imageInputPath, labelPath, size, threshold, imageOutput, annotationOutput)

