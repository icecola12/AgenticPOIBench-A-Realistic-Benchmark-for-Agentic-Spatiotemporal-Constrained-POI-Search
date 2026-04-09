"""
修改任务指令：你要找一家附近1公里内的咖啡厅，准备临时和客户签个合同。对方会从人民公园出发打车过来，所以你希望你步行到咖啡厅的时间，和对方打车到咖啡厅的时间相差不超过15分钟。咖啡厅本身的评分要在4.2分及以上，并且在今晚20:00之后仍然营业。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。
输入：B0I0KD1Y0A
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离(附近1公里)：调用 maps_around_search，以用户坐标126.987602,46.635993为中心、radius=1000、keywords=咖啡厅；验证返回pois列表中包含目标poi_id=B0I0KD1Y0A。
2) 评分>=4.2：调用 maps_search_detail(B0I0KD1Y0A)，读取biz_ext.rating，验证rating>=4.2。
3) 营业时间(今晚20:00后仍营业)：调用 maps_search_detail(B0I0KD1Y0A)，读取biz_ext.open_time 或 biz_ext.opentime2；验证其结束时间晚于20:00（例如08:30-20:30则满足）。
4) 与“人民公园”到店打车时间差<=15分钟：
a) 调用 maps_text_search(keywords=park_address, city=park_city) 取 poi_id，再 maps_search_detail(id=poi_id) 获取人民公园坐标；或直接用已知POI(人民公园 B0FFH6YYF8)的location作为对方出发点。
b) 调用 maps_walking_by_coordinates(origin=126.987602,46.635993, destination=目标POI location) 得到步行时长t_walk。
c) 调用 maps_driving_by_coordinates(origin=人民公园location, destination=目标POI location) 得到驾车时长t_drive。
d) 验证 |t_walk - t_drive| <= 15分钟（即<=900秒）。
（参考真实数据：目标POI评分4.3，open_time=08:30-20:30；用户步行约955秒；人民公园驾车约190秒，差值765秒<=900秒。）
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0I0KD1Y0A",
    user_location: str = "126.987602,46.635993",
    around_search_radius: str = "1000",
    around_search_keywords: str = "咖啡厅",
    min_rating: float = 4.2,
    park_address: str = "人民公园",
    park_city: str = "绥化市",
    park_location: str = "126.991560,46.616739",
    max_time_diff_seconds: int = 900
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    验证步骤：
    1) 距离(附近1公里)：验证POI是否在用户1公里范围内
    2) 评分>=4.2：验证POI评分是否满足要求
    3) 营业时间(今晚20:00后仍营业)：验证POI结束时间是否晚于20:00
    4) 与"人民公园"到店打车时间差<=15分钟：验证步行时间与驾车时间差是否在15分钟内
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标
        around_search_radius: 周边搜索半径
        around_search_keywords: 周边搜索关键词
        min_rating: 最低评分要求
        park_address: 人民公园地址
        park_city: 人民公园所在城市
        park_location: 人民公园位置坐标（如果获取失败则使用此默认值）
        max_time_diff_seconds: 最大时间差（秒），15分钟=900秒
    
    Returns:
        bool: 完全满足所有验证条件返回True，否则返回False
    """
    passed_count = 0
    total_count = 4
    
    # 实际用于后续计算的POI坐标，优先使用POI详情中的location
    actual_poi_location = None
    
    # 验证步骤1: 距离(附近1公里)验证
    print("验证步骤1: 距离(附近1公里)验证")
    print(f"调用 maps_around_search(location=\"{user_location}\", radius=\"{around_search_radius}\", keywords=\"{around_search_keywords}\")")
    around_result = maps_around_search(
        location=user_location,
        radius=around_search_radius,
        keywords=around_search_keywords
    )
    
    if around_result.error:
        print(f"周边搜索失败: {around_result.error}")
        print("验证步骤1: 未通过")
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"验证步骤1: 通过 - 在周边搜索结果中找到目标POI ID: {target_poi_id}")
            passed_count += 1
        else:
            print(f"验证步骤1: 未通过 - 在周边搜索结果中未找到目标POI ID: {target_poi_id}")
    
    # 验证步骤2: 评分>=4.2验证
    print("\n验证步骤2: 评分>=4.2验证")
    print(f"调用 maps_search_detail(id=\"{target_poi_id}\")")
    detail_result = maps_search_detail(id=target_poi_id)
    
    if detail_result.error:
        print(f"POI详情查询失败: {detail_result.error}")
        print("验证步骤2: 未通过")
    else:
        # 获取rating
        rating = None
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            rating_value = detail_result.biz_ext.get("rating")
            if rating_value is not None:
                try:
                    rating = float(rating_value)
                except (ValueError, TypeError):
                    pass
        
        if rating is not None:
            if rating >= min_rating:
                print(f"验证步骤2: 通过 - POI评分 {rating} >= {min_rating}")
                passed_count += 1
            else:
                print(f"验证步骤2: 未通过 - POI评分 {rating} < {min_rating}")
        else:
            print("验证步骤2: 未通过 - 无法获取POI评分信息")
        
        # 更新POI location（如果从详情中获取到了）
        if detail_result.location:
            actual_poi_location = detail_result.location
            print(f"从POI详情获取到location: {actual_poi_location}")
    
    # 验证步骤3: 营业时间(今晚20:00后仍营业)验证
    print("\n验证步骤3: 营业时间(今晚20:00后仍营业)验证")
    if detail_result.error:
        print("验证步骤3: 未通过 - POI详情查询失败，无法获取营业时间")
    else:
        # 获取营业时间
        open_time_str = None
        if detail_result.biz_ext and isinstance(detail_result.biz_ext, dict):
            # 优先尝试 open_time，如果没有则尝试 opentime2
            open_time_str = detail_result.biz_ext.get("open_time")
            if not open_time_str:
                open_time_str = detail_result.biz_ext.get("opentime2")
        
        if open_time_str:
            # 解析营业时间，格式可能是 "08:30-20:30" 或类似
            try:
                # 提取结束时间
                if "-" in open_time_str:
                    time_parts = open_time_str.split("-")
                    if len(time_parts) >= 2:
                        end_time_str = time_parts[-1].strip()
                        # 解析结束时间（格式可能是 "20:30"）
                        if ":" in end_time_str:
                            end_hour_min = end_time_str.split(":")
                            if len(end_hour_min) >= 2:
                                end_hour = int(end_hour_min[0])
                                end_min = int(end_hour_min[1])
                                # 转换为分钟数进行比较（20:00 = 20*60 = 1200分钟）
                                end_minutes = end_hour * 60 + end_min
                                required_minutes = 20 * 60  # 20:00 = 1200分钟
                                
                                if end_minutes > required_minutes:
                                    print(f"验证步骤3: 通过 - 营业结束时间 {end_time_str} 晚于20:00")
                                    passed_count += 1
                                else:
                                    print(f"验证步骤3: 未通过 - 营业结束时间 {end_time_str} 不晚于20:00")
                            else:
                                print("验证步骤3: 未通过 - 无法解析营业时间格式")
                        else:
                            print("验证步骤3: 未通过 - 营业时间格式不正确")
                    else:
                        print("验证步骤3: 未通过 - 营业时间格式不正确")
                else:
                    print("验证步骤3: 未通过 - 营业时间格式不正确（缺少分隔符）")
            except (ValueError, IndexError) as e:
                print(f"验证步骤3: 未通过 - 解析营业时间失败: {e}")
        else:
            print("验证步骤3: 未通过 - 无法获取POI营业时间信息")
    
    # 验证步骤4: 与"人民公园"到店打车时间差<=15分钟验证
    print("\n验证步骤4: 与\"人民公园\"到店打车时间差<=15分钟验证")
    if not actual_poi_location:
        print("验证步骤4: 未通过 - 无法获取POI坐标，无法计算时间差")
    else:
        # 步骤4a: 获取人民公园坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
        park_text_result = maps_text_search(keywords=park_address, city=park_city)
        park_coord = park_location  # 默认使用提供的坐标
        if park_text_result.error:
            print(f"地理编码失败: {park_text_result.error}")
            print(f"使用默认坐标: {park_coord}")
        else:
            if park_text_result.pois and len(park_text_result.pois) > 0:
                first_poi_id = park_text_result.pois[0].id
                park_detail_result = maps_search_detail(id=first_poi_id)
                if park_detail_result.error:
                    print(f"❌ 获取坐标失败: {park_detail_result.error}")
                    return False
                if not park_detail_result.location:
                    print("❌ 未获取到坐标")
                    return False
                park_coord = park_detail_result.location
                print(f"获取到人民公园坐标: {park_coord}")
            else:
                print(f"未找到人民公园坐标，使用默认坐标: {park_coord}")
        
        # 步骤4b: 计算用户步行到POI的时间
        print(f"调用 maps_walking_by_coordinates(origin=\"{user_location}\", destination=\"{actual_poi_location}\")")
        walking_result = maps_walking_by_coordinates(
            origin=user_location,
            destination=actual_poi_location
        )
        
        if walking_result.error:
            print(f"步行路线规划失败: {walking_result.error}")
            print("验证步骤4: 未通过")
        else:
            t_walk = walking_result.total_duration_seconds
            if t_walk is None:
                print("验证步骤4: 未通过 - 无法获取步行时间")
            else:
                print(f"用户步行到POI的时间: {t_walk}秒")
                
                # 步骤4c: 计算从人民公园驾车到POI的时间
                print(f"调用 maps_driving_by_coordinates(origin=\"{park_coord}\", destination=\"{actual_poi_location}\")")
                driving_result = maps_driving_by_coordinates(
                    origin=park_coord,
                    destination=actual_poi_location
                )
                
                if driving_result.error:
                    print(f"驾车路线规划失败: {driving_result.error}")
                    print("验证步骤4: 未通过")
                else:
                    t_drive = driving_result.total_duration_seconds
                    if t_drive is None:
                        print("验证步骤4: 未通过 - 无法获取驾车时间")
                    else:
                        print(f"从人民公园驾车到POI的时间: {t_drive}秒")
                        
                        # 步骤4d: 验证时间差
                        time_diff = abs(t_walk - t_drive)
                        if time_diff <= max_time_diff_seconds:
                            print(f"验证步骤4: 通过 - 时间差 {time_diff}秒 <= {max_time_diff_seconds}秒")
                            passed_count += 1
                        else:
                            print(f"验证步骤4: 未通过 - 时间差 {time_diff}秒 > {max_time_diff_seconds}秒")
    
    # 输出最终结果
    print(f"\n验证完成: 通过 {passed_count}/{total_count} 项验证")
    if passed_count == total_count:
        print("最终验证结果: True (完全满足所有验证条件)")
        return True
    else:
        print("最终验证结果: False (部分满足或不满足验证条件)")
        return False


def main():
    result = verify_poi()
    print(f"\n函数返回值: {result}")  


if __name__ == "__main__":
    main()
