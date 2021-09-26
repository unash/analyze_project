#!/usr/bin/python3

"""
* Function: Analyze an iOS project
* Author: UnAsh
* Blog: https://blog.exbye.com
* Github: https://github.com/unash/analyze_project
* Licence: GPL-3.0
"""

from graphviz import Digraph, Graph
import sys
import os
import time
import shutil
import re

ignore_dirs = ['Pods']
ignore_nodes = ['NSObject']

######################### 工具区 #########################

def get_all_header_files(folder):
    """获取所有头文件"""
    entries = os.listdir(folder)
    files = []
    for entry in entries:
        entry_path = folder+'/'+entry
        if os.path.isdir(entry_path):
            if not is_ignore_dir(entry): # 忽略依赖
                sub_entries = get_all_header_files(entry_path)
                for sub_entry in sub_entries:
                    files.append(sub_entry)
        elif is_header_file(entry_path):
            files.append(entry_path)
    return files

def is_header_file(file):
    """判断是否是头文件"""
    return file.endswith('.h') or file.endswith('.swift')

def is_ignore_dir(folder):
    return is_in_list(ignore_dirs, folder)

def is_ignore_node(node):
    return is_in_list(ignore_nodes, node)

def is_in_list(list, item):
    for entry in list:
        if entry==item:
            return True
    return False

######################### 基类区 #########################

re_flags = re.I|re.M|re.S|re.U
re_node_name = r'([0-9a-zA-Z_]+)'

class Processor:
    def analyze_class(self, content, class_nodes, class_edges, protocol_nodes):
        pass
    def analyze_protocol(self, content, protocol_nodes, protocol_edges):
        pass

######################### Swift区 #########################

class SwiftProcessor(Processor):

    other_info_pattern = r'(\s*[:]\s*([0-9a-zA-Z_, ]+))?\s+[{]\n'
    class_pattern = re.compile(r'class'+r'\s+'+re_node_name+other_info_pattern)
    protocol_pattern = re.compile(r'protocol'+r'\s+'+re_node_name+other_info_pattern)

    def analyze_class(self, content, class_nodes, class_edges, protocol_nodes):
        for m in self.class_pattern.finditer(content):
            print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
            class_node = m.group(1)
            class_nodes.add(class_node)
            if len(m.groups()) == 3 and m.group(3) != None: # 有其他信息
                componentsStr = m.group(3)
                for index,component in enumerate(componentsStr.strip(' ').split(',')):
                    super_node = component.strip(' ')
                    if super_node!=None and len(super_node)>0 and not is_ignore_node(super_node):
                        if index == 0: # 这种判断很不准确
                            class_nodes.add(super_node)
                        else:
                            protocol_nodes.add(super_node)
                        class_edges.append([class_node, super_node])
    def analyze_protocol(self, content, protocol_nodes, protocol_edges):
        for m in self.protocol_pattern.finditer(content):
            print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
            protocol_node = m.group(1)
            protocol_nodes.add(protocol_node)
            if len(m.groups()) == 3 and m.group(3) != None: # 有其他信息
                componentsStr = m.group(3)
                for index,component in enumerate(componentsStr.strip(' ').split(',')):
                    super_node = component.strip(' ')
                    if super_node!=None and len(super_node)>0 and not is_ignore_node(super_node):
                        protocol_nodes.add(super_node)
                        protocol_edges.append([protocol_node, super_node])

######################### OC区 #########################

class OCProcessor(Processor):

    re_class_prefix = r'@interface'
    re_protocol_prefix = r'@protocol'
    re_protocol_block = r'(\<[0-9a-zA-Z_,\s]+\>)?'

    # 类
    class_pattern = re.compile(re_class_prefix+r'\s+'+re_node_name+r'\s*:\s*'+re_node_name+r'\s*'+re_protocol_block,flags=re_flags)
    # 分类
    category_pattern = re.compile(re_class_prefix+r'\s+'+re_node_name+r'\s*(\('+re_node_name+r'\))?\s*'+re_protocol_block,flags=re_flags)
    # 协议
    protocol_pattern = re.compile(re_protocol_prefix+r'\s+'+re_node_name+r'\s*'+re_protocol_block,flags=re_flags)

    def analyze_class(self, content, class_nodes, class_edges, protocol_nodes):
        """分析类结构"""
        for m in self.class_pattern.finditer(content):
            print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
            class_node = m.group(1)
            super_class_node = m.group(2)
            protocol_list = m.group(3)
            class_nodes.add(class_node)
            if super_class_node!=None and len(super_class_node)>0 and not is_ignore_node(super_class_node):
                class_edges.append([class_node, super_class_node])
            if protocol_list!=None and len(protocol_list)>0:
                for protocol_str in protocol_list.strip('<> ').split(','):
                    protocol_node = protocol_str.strip()
                    if len(protocol_node)>0 and not is_ignore_node(protocol_node):
                        protocol_nodes.add(protocol_node)
                        class_edges.append([class_node, protocol_node])
        for m in self.category_pattern.finditer(content):
            print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
            class_node = m.group(1)
            protocol_list = m.group(4)
            if protocol_list!=None and len(protocol_list)>0:
                for protocol_str in protocol_list.strip('<> ').split(','):
                    protocol_node = protocol_str.strip()
                    if len(protocol_node)>0 and not is_ignore_node(protocol_node):
                        protocol_nodes.add(protocol_node)
                        class_edges.append([class_node, protocol_node])

    def analyze_protocol(self, content, protocol_nodes, protocol_edges):
        """分析协议结构"""
        for m in self.protocol_pattern.finditer(content):
            print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
            protocol_node = m.group(1)
            protocol_nodes.add(protocol_node)
            protocol_list = m.group(2)
            if protocol_list!=None and len(protocol_list)>0:
                for protocol_str in protocol_list.strip('<> ').split(','):
                    super_protocol_node = protocol_str.strip()
                    if len(super_protocol_node)>0 and not is_ignore_node(super_protocol_node):
                        protocol_nodes.add(super_protocol_node)
                        protocol_edges.append([protocol_node, super_protocol_node])

######################### 主控区 #########################

def main(root_path, output_path):
    """主函数"""
    print("Start analyzing classes...")
    print('Root Path: ', root_path)
    print('Output Path: ', output_path)
	# Main Digraph
    G = Digraph('image', engine='dot', strict=True, format='pdf')
    G.graph_attr['label'] = 'Project Digraph'
    G.layout = 'dot'
    G.graph_attr['rankdir'] = 'LR'
    G.node_attr['style'] = 'filled'
    
    class_nodes = set([]) # 类集合
    protocol_nodes = set([]) # 协议集合
    class_edges = [] # 类结构
    protocol_edges = [] # 协议结构

    files = get_all_header_files(root_path)
    processors = {'oc':OCProcessor(), 'swift':SwiftProcessor()}
    for file in files:
        filetype = 'oc'
        if (file.endswith('.swift')):
            filetype = 'swift'
        processor = processors[filetype]
        file_handler = open(file)
        content = file_handler.read()
        processor.analyze_class(content, class_nodes, class_edges, protocol_nodes)
        processor.analyze_protocol(content, protocol_nodes, protocol_edges)
        file_handler.close()

    # class subgraph
    C = Digraph('r2_classes')
    C.node_attr['color']='#3399FF'
    C.node_attr['shape']='Mrecord'
    
    for node in class_nodes:
        C.node(node)
    for edge in class_edges:
        C.edge(edge[0],edge[1])

    # Test
    # C.node('b')
    # C.node('c')
    # C.edge('b','c')
    
    # protocol subgraph
    P = Digraph('r1_protocol')
    P.node_attr['shape'] = 'rect'
    P.node_attr['color'] = '#00CC66'
    
    for node in protocol_nodes:
        P.node(node)
    for edge in protocol_edges:
        P.edge(edge[0],edge[1])

    G.subgraph(P)
    G.subgraph(C)
    
    #G.view()
    G.render(filename=output_path+'/project', view=True, cleanup=True)
    print('Process Finished!')

def print_usage():
    usage = "Bad Parameters! Format follows: \n"
    usage += " python analyze_project.py dir1 dir2 \n where: \n"
    usage += "  dir1: project directory \n"
    usage += "  dir2: output directory \n"
    print(usage)

if __name__ == "__main__":
    PATH = sys.path[0]
    OUTPUT_PATH = PATH

    # debug
    #PATH = '/Users/UnAsh/HomeSpace/Projects/github_ios/AsyncDisplayKit'
    #OUTPUT_PATH = '/Users/UnAsh/Desktop/analyse_project'

    if len(sys.argv) >= 2:
        PATH = sys.argv[1]
        OUTPUT_PATH = PATH
        current_time = time.strftime('%Y%m%d', time.localtime(time.time()))
        if len(sys.argv) >= 3:
            OUTPUT_PATH = sys.argv[2]
    else:
        print_usage()
        exit(0)
    os.chdir(PATH)
    main(PATH, OUTPUT_PATH)
