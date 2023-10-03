# RSS-Master

针对RSS源的自定义过滤、筛选，使用AI总结、概括、打分等

### 前言

9月初旬，我开始使用Inoreader + RSSHub 来聚合、订阅我感兴趣的RSS，配合Reeder阅读，试图完全掌控每日输入的信息源头，一个月下来，逐渐增多的RSS源，日益增加的未读信息，给我增添了不少阅读焦虑，于是想着是否有方式可以自定义一些过滤规则的，最好能加入AI来辅助我阅读，减少我阅读的负担。

Inoreader自带有过滤器，但仅仅为这个功能买单感觉有点不划算; NewsBlur有「Intelligence Trainer」来做智能分类，但我简单尝试了下感觉反馈不明显，短时间内体现不出智能；Feedly既有筛选还有AI功能，听起来很满足我的需求，正当我踌躇要不要从Inoreader转到Feedly的付费用户的时候，我看到了这两个项目

- [让 ChatGPT 帮我们总结 Hacker News](https://blog.betacat.io/post/2023/06/summarize-hacker-news-by-chatgpt/)
- [RSS-GPT 使用指南](http://yinan.me/rss-gpt-manual-zh.html)

这两个项目的总体思路都是通过GitAction去执行一个脚本，获取信息后使用Open AI的API进行翻译、总结，然后渲染成模板，部署到GitHub Page上。RSS-GPT中的方式会更加满足我的需求，通过定时执行脚本直接获取RSS的xml文件，处理后把xml部署到GitHub Page上后，就可以得到这个xml文件的访问链接，最后让阅读器直接订阅这个链接即可。

我在[RSS-GPT](https://github.com/yinan-c/)的思路上做了扩展，叫做RSS-Master，它有如下特点

- 支持opml文件和config文件的相互转换：`script/convert_opml_to_yaml.sh` `script/convert_yaml_to_opml.sh`

- 支持自定义筛选规则：目前支持include、exclude两种类型，title和article两种作用域

  - ```
    - htmlUrl: http://www.smzdm.com
      name: c5738f
      text: 什么值得买 | 优惠精选
      url: http://feed.smzdm.com
      filters:
        - type: include
          field: title
          keywords: ["可乐", "雪碧", "芬达", "柠檬", "茶叶", "纸巾", "酒精", "湿纸巾", "餐巾纸"]
    ```

- 支持RSS源内容的自动更新，更新内容展示在[这个地址](https://www.dcts.top/rssdocs/)

### 使用截图

- AI概括、摘要功能

<img src="https://qiniu.dcts.top/typora/202310031757486.png" alt="image-20231003174334231" style="zoom:50%;" />

<img src="https://qiniu.dcts.top/typora/202310031757686.png" alt="image-20231003175143405" style="zoom:50%;" />

- 自定义筛选：过滤「什么值得买」的好价频道，只推荐近期想屯的货，如汽水

<img src="https://qiniu.dcts.top/typora/%E4%BB%80%E4%B9%88%E5%80%BC%E5%BE%97%E4%B9%B0-%E6%B1%BD%E6%B0%B4.png" alt="image-20231003164248923" style="zoom: 50%;" />
