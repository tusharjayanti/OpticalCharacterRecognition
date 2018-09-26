import os
import sys
import math
import time
from random import shuffle
from PIL import Image

def detect_twist_direction(im):
    cycle = 92
    value = 0
    count = 0
    
    for i in range(cycle/2):
        for j in range(im.size[1]):
            if im.getpixel((i, j)) < 200:
                value += j
                count += 1
    avg_value = value / count
    #print 'avg_value'
    #print avg_value
    if avg_value >= 25:
        direction = -1
    else:
        direction = 1

    return direction

def get_shift_value(x, direction):
    if direction == 1:
        n = 2 * math.pi * (x) / 92
    else:
        n = 2 * math.pi * (x - 46) / 92

    return int(15 * math.sin(n))

# using sin function: 15 * sin (2pi * (x - 46) / 92), 2 pi = 92
def remove_twist(im):
    direction = detect_twist_direction(im)

    for i in range(im.size[0]):
        shift = get_shift_value(i, direction)
        if shift == 0:
            continue
        new_content = [255] * im.size[1]
        for j in range(im.size[1]):
            if im.getpixel((i, j)) < 200:
                if j + shift < im.size[1] and j + shift > 0:
                    new_content[j + shift] = im.getpixel((i, j))
        for j in range(im.size[1]):
            im.putpixel((i, j), new_content[j])

def count_pixel(im, loc):
    ret = 0

    for j in range(-1, 2):
        for i in range(-1, 2):
            if loc[0] + j > im.size[0] - 1 or loc[0] + j < 0:
                continue
            if loc[1] + i > im.size[1] - 1 or loc[1] + i < 0:
                continue
            if im.getpixel((loc[0] + j, loc[1] + i)) < 200:
                ret += 1

    return ret

def cut_into_chars(path, file_name, index, im, start, end):
    pixel_list = []
    for j in range(im.size[1]):
        for i in range(start, end):
            pixel_list.append(im.getpixel((i, j)))
    im2 = Image.new(im.mode, ((end - start), im.size[1]))
    im2.putdata(pixel_list)
    file_name = file_name.replace('.png', '-' + str(index) + '.png')
    im2.save(path + '/' + file_name, 'PNG')

def remove_noise(folder_name):
    new_folder = 'de-noised'
    chars_path = new_folder + '/chars'

    cwd = os.getcwd()
    print cwd

    #file_list = os.listdir(folder_name)[0:10]
    file_list = os.listdir(folder_name)
    print file_list
    os.chdir(folder_name)
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)
    if not os.path.exists(chars_path):
        os.makedirs(chars_path)

    for file_name in file_list:
        if '.png' not in file_name:
            continue
        im = Image.open(file_name).convert('L')
        im.load()
        """
        print im.format
        print im.size
        print im.size[0]
        print im.size[1]
        print im.mode"""
        r = im.getpixel((0,0))
        print r

        for i in range(im.size[1]):
            for j in range(im.size[0]):
                if im.getpixel((j, i)) >= 215:
                    im.putpixel((j, i), 255)
                # carefully select the range, might cause missing data
                elif im.getpixel((j, i)) <= 200:
                    count = count_pixel(im, (j, i))
                    if count <= 4:
                        im.putpixel((j, i), 255)
                

        remove_twist(im)
        im.save(new_folder + '/' + file_name, 'PNG')
        histogram = []
        for i in range(im.size[0]):
            sum_num = 0
            for j in range(im.size[1]):
                if im.getpixel((i, j)) < 200:
                    sum_num += 1
            histogram.append(sum_num)
        print histogram

        start = None
        index = 1
        for i in range(len(histogram)):
            if histogram[i] < 2:
                if start != None:
                    end = i
                    cut_into_chars(chars_path, file_name, index, im, start, end)
                    index += 1
                    start = None
                    end = None
                continue
            if start == None:
                start = i

    os.chdir(cwd)    

def extract_features(folder_name, data_points):
    icon_dir = 'thum'

    cwd = os.getcwd()
    print cwd

    file_list = os.listdir(folder_name)
    print file_list
    os.chdir(folder_name)
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)

    re_size_width = 12
    re_size_height = 50
    re_size = (12, 50)

    for file_name in file_list:
        data_point = []

        if '.png' not in file_name:
            continue
        im = Image.open(file_name).resize(re_size)
        im.load()
        print im.format
        print im.size
        print im.mode
        r = im.getpixel((0,0))
        print r

        # calculate horizon sum
        for i in range(re_size_width):
            sum = 0
            for j in range(re_size_height):
                if im.getpixel((i, j)) < 200:
                    sum += 1
            data_point.append(sum)

        # calculate vertical sum
        for i in range(re_size_height):
            sum = 0
            for j in range(re_size_width):
                if im.getpixel((j,i)) < 200:
                    sum += 1
            data_point.append(sum)

        im.save(icon_dir + '/' + file_name, 'PNG')
        """if is_class_label == True:
            data_point.append(1)
        else:
            data_point.append(0)"""

        print data_point
        print len(data_point)
        data_points.append(data_point)

    os.chdir(cwd)   

def read_data(file_name, is_class=False):
    input_data = open(file_name, 'r')
    lines = input_data.read().split('\n')
    data_points = []
    for line in lines:
        values = line.split(' ')
        try:
            converted_values = [float(i) for i in values]
            if is_class:
                converted_values.append(1.0)
            else:
                converted_values.append(0.0)
            data_points.append(converted_values)
        except ValueError,e:
            #print "error",e,"on line",i
            #time.sleep(1)
            continue
    input_data.close()

    return data_points

def output_data(item_list, file_name):
    output_file = open(file_name, 'w')
    for item in item_list:
        string = str(item).replace('[', '').replace('.0]', '').replace(',', '').replace(']', '')
        print>>output_file, string
    output_file.close()

# calculate the probability of y = 1
def calculate_p_y_1(data_point, w_list):
    score = 0
    for i in range(len(w_list)):
        if i == 0:
            score += w_list[0]
        else:
            score += w_list[i] * data_point[i - 1]

    p = float(1) / (1 + math.exp(-1 * score))

    return p

def get_p_list(data_points, w_list):
    p_list = []
    for i in range(len(data_points)):
        p_list.append(calculate_p_y_1(data_points[i], w_list))

    return p_list

def calculate_acc(data_points, p_list):
    correct_counts = 0
    true_positive_counts = 0

    for i in range(len(p_list)):
        if p_list[i] >= 0.5 and data_points[i][-1] == 1:
            correct_counts += 1
            true_positive_counts += 1
        elif p_list[i] < 0.5 and data_points[i][-1] == 0:
            correct_counts += 1
    accuracy = float(correct_counts) / len(p_list)

    return accuracy, true_positive_counts

def calculate_der(data_point, w_list, p):
    der_w_list = []
    for i in range(len(w_list)):
        if i == 0:
            h_x = 1
        else:
            h_x = data_point[i - 1]
        der_w = h_x * (bool(data_point[-1]) - p)
        der_w_list.append(der_w)

    return der_w_list

def get_total_der_w(data_points, w_list, p_list):
    # initial value of 0s
    total_der_w = [0] * len(w_list)

    for j in range(len(p_list)):
        der_w_list = calculate_der(data_points[j], w_list, p_list[j])
        for i in range(len(w_list)):
            total_der_w[i] += der_w_list[i]

    return total_der_w

# the stop condition is meet when all absolute values of w list
# are smaller than the target value
def is_stop_condition(target, total_der_w):
    for der_w in total_der_w:
        if abs(der_w) >= target:
            return False

    return True

def initial_run(data_points, true_label_num):
    # start point of w list on the initial run is set to 0
    global label
    w_list = [0] * len(data_points[0])
    # step can not go over 0.00005
    #step = 0.00003
    step = 0.00005

    print 'performing Gradient Decent Algorithms ... '
    count = 0
    while True:
        p_list = get_p_list(data_points, w_list)
        total_der_w = get_total_der_w(data_points, w_list, p_list)
        for i in range(len(w_list)):
            w_list[i] += step * total_der_w[i]

        # only for test and debug
        if count >= 200:
            acc, true_positives = calculate_acc(data_points, p_list)
            print 'training label:'
            print label
            print 'accuracy:'
            print acc
            print 'true positive counts:'
            print str(true_positives) + '/' + str(true_label_num)
            print 'the list of derivation on w:'
            if len(total_der_w) > 10:
                #print total_der_w[0:10]
                print total_der_w
            else:
                print total_der_w
            print 'w list:'
            print w_list
            count = 0
            #time.sleep(2)

        count += 1
        if is_stop_condition(0.5, total_der_w):
            print 'a stop condition has been met'
            acc, true_positives = calculate_acc(data_points, p_list)
            print 'training label:'
            print label
            print 'accuracy:'
            print acc
            print 'true positive counts:'
            print str(true_positives) + '/' + str(true_label_num)
            print 'the list of derivation on w:'
            print total_der_w
            print 'w list:'
            print w_list
            break

    return w_list, acc, true_positives

def validation_run(data_points):
    # step size of gradient decent is set to 0.002
    step = 0.000003
    accuracy_list = []

    for round_num in range(1, 11):
        # shuffle the data set before each validation run
        shuffle(data_points)

        # construct the output file name
        # these output files are used for recording test sets on each round
        # it would be convenient if we want to reproduce the result using these sets
        file_name = 'data_' + str(round_num) + '.txt'
        output_data(data_points, file_name)
        test_data = data_points[0:len(data_points)/10]
        training_data = data_points[len(data_points)/10:-1]

        # recording test data
        file_name = 'test_data_' + str(round_num) + '.txt'
        output_data(test_data, file_name)
        # recording training data
        file_name = 'training_data_' + str(round_num) + '.txt'
        output_data(training_data, file_name)

        # set a closer start point based on results of initial runs
        w_list = [1.8768604185163993, -0.03161809843292117, -0.03486845549180967, 0.006812927021954209, 0.05207647039334728, 0.07393363266894899, -0.019297509166874994, -0.09844644771142888, -0.15893176219251548, 0.052851326036999845, 0.03778659811954229, -0.02922609851647949, 0.011646676323988157, 0.014311699199866966, 0.000684060264673086, 0.0672060560695011, 0.018271486600060772, 0.012672753336994172, -0.03787145584360085, -0.07257267755744998, 0.04798730465081442, 0.000996692933123403, -0.1331466318769129, 0.1335558300534257, 0.06341227236628609, 0.01233239236146354, -0.05904634276491596, 0.0718792487965464, 0.04372747776648773, -0.042913181659186006, -0.03877670117048354, -0.05429934496710391, 0.0339672838915455, 0.03125025773521783, -0.017014898923967153, 0.0894214451337118, 0.059846032508346296, -0.0041868936060916575, -0.06655422700771929, -0.07971671240959158, 0.07543537335658282, 0.0056351815084742796, -0.0017706729260718657, -0.02510170190732859, -0.0242615852534958, -0.012552540191480622, 0.002679009132354028, 0.007922071205092487, 0.07417662389271437, 0.002053407777340997, -0.08123956830598393]

        while True:
            p_list = get_p_list(training_data, w_list)
            total_der_w = get_total_der_w(training_data, w_list, p_list)
            for i in range(len(w_list)):
                w_list[i] += step * total_der_w[i]

            # check if the stop condition is meet
            if is_stop_condition(0.5, total_der_w):
                print 'accuracy on training data:'
                print calculate_acc(training_data, p_list)
                print 'the list of derivation on w:'
                print total_der_w
                print 'w list:'
                print w_list
                break

        print 'finished training'
        print 'now feeding the test data ...'
        time.sleep(1)

        p_list = get_p_list(test_data, w_list)
        print 'accuracy on test data:'
        acc = calculate_acc(test_data, p_list)
        print acc
        accuracy_list.append(acc)
        print 'starting next round in 3 secs ... \n'
        time.sleep(3)

    print 'all rounds finished'
    print 'the accuracy list:'
    print accuracy_list
    print 'the average accuracy:'
    print sum(accuracy_list) / len(accuracy_list)

def gather_data_points(path):
    folder_list = os.listdir(path)
    for folder_name in folder_list:
        if folder_name == '.' or folder_name == '..':
            continue
        data_points = []
        extract_features(path + '/' + folder_name, data_points)
        if not os.path.exists('data_points'):
            os.makedirs('data_points') 
        output_data(data_points, 'data_points/' + folder_name + '.txt')

def read_data_points(path, label):
    print 'reading the data points ...'
    data_points = read_data(path + '/' + label + '.txt', True)
    true_label_num = len(data_points)
    #data_points.extend(read_data(path + '/b.txt', False))
    #data_points.extend(read_data(path + '/c.txt', False))
    #data_points.extend(read_data(path + '/d.txt', False))
    file_list = os.listdir(path)
    print file_list
    for item in file_list:
        if item == '.' or item == '..':
            continue
        if item == label + '.txt':
            # do not load the label data again
            continue

        data = read_data(path + '/' + item, False)
        if data == []:
            print item + ' skipped'
            continue
        data_points.extend(data)

    return data_points, true_label_num

def save_w_list(w_list, acc, true_positives, true_label_num, label):
    if not os.path.exists('w_list'):
        os.makedirs('w_list')
    file_name = 'w_list/w_list_' + label + '.txt'
    output_data(w_list, file_name)

    file_name = 'w_list/accuracy_' + label + '.txt'
    output_file = open(file_name, 'w')
    print>>output_file, acc
    print>>output_file, str(true_positives) + '/' + str(true_label_num)
    output_file.close()

def load_w_list(label):
    if not os.path.exists('w_list'):
        print 'w_list folder doest not exist'
        return

    w_list = []
    input_data = open('w_list/w_list_' + label + '.txt', 'r')
    lines = input_data.read().split('\n')
    for line in lines:
        try:
            converted_values = float(line)
            w_list.append(converted_values)
        except ValueError,e:
            #print "error",e,"on line",i
            continue

    input_data.close()

    return w_list

def demo_run():

    return

# mapping function probility -> 1 / ( 1 - e^-score(x))
# score(x) = w0 + w1*x1 + w2*x2 + w3*x3 + w4*x4

#remove_noise('captcha/captcha')
#gather_data_points('captcha/class')
label = '6'
data_points, true_label_num = read_data_points('data_points', label)
print 'number of data points read:'
print len(data_points)
print 'number of true labeled data:'
print true_label_num
print 'label'
print label
print ''

# read all data from the file
mode = input('Choose the task: \n(1) initial run using all data set \n(2) validation runs with randomly selected training data \n(3) demo runs to classfy the character images at given location \n')

if mode == 1:
    w_list, acc, true_positives = initial_run(data_points, true_label_num)
    save_w_list(w_list, acc, true_positives, true_label_num, label)
elif mode == 2:
    w_list = load_w_list(label)
    validation_run(data_points)
elif mode == 3:
    demo_run()
else:
    print 'invalid input'
    sys.exit(0)
