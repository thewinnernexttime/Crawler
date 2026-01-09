curl 'https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary&q=%E7%AE%A1%E7%90%86%E6%9D%A1%E4%BE%8B&timetype=timeqb&mintime=&maxtime=&sort=score&sortType=1&searchfield=title&pcodeJiguan=&childtype=&subchildtype=&tsbq=&pubtimeyear=&puborg=&pcodeYear=&pcodeNum=&filetype=&p=1&n=5&inpro=&bmfl=&dup=&orpro=&type=gwyzcwjk' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -b 'wdcid=6f8bb86d9f9d20c1; tfstk=glTmnrf87TwQL2yr-R7j0mTCSlmRcZ_1IdUOBNBZ4TW7DrhfX32wTBswHZC9qOvlFrUAkZlMIpJcXdAsG1WwQdX9D03pGI_17vdiJ2dfZyG7yKfV3alN_szqwiyNNVZP7vHKyY3K29QwMx9NSQRPF14NgiJNa7W5To7N3Gyz46WPQNJN0_RPtsq4gizV4bf1Us7N7dRrZ1BPQN7wQQlg9YBA3OTrBVewT66GoUfcm9RoAP4aMsydpIJUSPXciimkgT4a7UxwJZR1K42PeCRBbgYiyz_6wHvMbLla7OxPtpfpH4zc73Jk-MRSKr6D4KTGkMggs_xHaKYDZfEkILRBAZ8qCrBXbQ8NeElTS9-pOafWWYaVI3-wki__3xfkoBYMjgub4kuSLP1r6Ur_fi55Z9e87liE8r-1kbcuYsjVNsz-Zbqsoi55Z9hoZk8h0_14y; ariatheme=0; ariaStatus=false; ariafontScale=1' \
  -H 'Pragma: no-cache' \
  -H 'Referer: https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q=&t=zhengcelibrary&orpro=' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"'

  # F12
  # Network
  # 勾选 Preserve log 和 Disable cache
  # 点击 Network 左上角的 Clear 按钮
  # 在搜索框输入 "管理条例" ，触发一次搜索
  # （可选）Network 上方有类型分类（All / Fetch/XHR / Doc / JS / CSS / Img ...），选择 Fetch/XHR，这样就去除了图片、css、js等文件的噪声
  # （可选）点开请求，查看右侧的 Initiator（发起程序 / 调用者），如果调用者是 main.js，script.js，bundle.js，则说明是页面逻辑发起的API
  # （可选）请求的 Preview 和 Response 能展开 Json，则说明是我们在找的接口
  # 找到真正请求后，右键选中，选择 Copy -> Copy as cURL (bash)，复制出来
  # 复制出来的就是以上可用的 curl 命令
  # 把 Cookie 等参数从 curl 迁移到 Python 脚本，爬虫就大功告成了