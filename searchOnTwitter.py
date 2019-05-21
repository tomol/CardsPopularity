# -*- coding:utf-8 -*-
import json, settings
import chengeHanToZen
import raritysArray
import re
import sys
from requests_oauthlib import OAuth1Session
from janome.tokenizer import Tokenizer


"""
カード名をtxtから全て取得
"""
def getCardList():
    cardList = []
    f = open('cardListReplaced.txt', encoding='utf-8')
    listnames = f.readline()
    while listnames:
        cardList.append(listnames.replace('\n', ''))
        listnames = f.readline()
    f.close()
    return cardList


"""
形態素解析にかけた行からカード名の一部と思われる部分のみを抜き出し、それを配列にして返す
"""
def matchPieses(lineAnalyze):
    restoreArray = []
    for token in lineAnalyze:
        partOfSpeech0 = token.part_of_speech.split(',')[0]
        partOfSpeech2 = token.part_of_speech.split(',')[2]

        #名詞、組織でない部分は除外
        if partOfSpeech0 != u'名詞':
            continue
        if partOfSpeech2 == u'組織':
            continue

        #「・」や「ー」のせいでうまく検索できない可能性があるため、空白に置き換える
        result = token.surface.replace('・', '')

        #半角カナを全角に、全角英字を半角に変換
        chengedResult = chengeHanToZen.Han2Zen(result, chengeHanToZen.KANA)
        chengedResult = chengeHanToZen.Zen2Han(chengedResult, chengeHanToZen.ASCII|chengeHanToZen.DIGIT)

        #配列として抽出要素を保存
        restoreArray.append(chengedResult)
    return  restoreArray


"""
カードリストからツイートにあった文字を完全に含んでるカード名を取り出す
"""
def checkList(pieces, cardList, pieceNumber):
    resultCardList = []             #検索してヒットしたカード名を保存するリスト
    nextNumber = pieceNumber + 1    #配列の次

    if pieces == []:                #ツイートにあった言葉の配列が空だったら存在しないと返す
        return 'not exist'

    for name in cardList:
        #ツイートにあった言葉が入っている名前があれば別配列に保存
        if name.find(pieces[pieceNumber]) >= 0:
            resultCardList.append(name)

    #カード名がただ一つに決まった場合は、決まった段階の言葉「以降」の言葉を別の配列に入れて返す
    if len(resultCardList) == 1:
        notNamePieces = pieces[nextNumber:]
        unionArray = []
        unionArray.append(resultCardList[0])
        unionArray.append(notNamePieces)
        return unionArray

    #ツイートにあった言葉を検索し終え、かつ残ったカード名が一件ならそれを、一件でなければ存在しないことを返す
    if len(pieces) == nextNumber:
        return 'not exist'

    #条件に合致しなければ検索結果のリストで再帰
    if len(resultCardList) > 0:
        return checkList(pieces, resultCardList, nextNumber)
    else:
        return 'not exist'


"""
買取金額のみを取り出す
"""
def onlyValues(notNamePieces, pattern):
    value = []

    for checkNow in notNamePieces:

        rarityPattern = pattern
        if re.findall(rarityPattern, checkNow) != []:
            break

        #'円'や'\'が含まれている可能性があるので、正規表現で数字のみ取得
        pattern = r'([0-9]+)'
        value = re.findall(pattern, checkNow)

        if value != []:
            return value[0]

    return "No Value"


"""
対象のカード名の買取金額のみの配列を作成
"""
def makeNewArrayOfValue(nameAndValuesArray, checkWord, pattern):
    onlyValuesArray = []
    for nameAndValuesArray in results:

        #検索対象と同じ名前のカードのみに処理をする
        if nameAndValuesArray[0] == checkWord:
            values = onlyValues(nameAndValuesArray[1], pattern)
            if values != "No Value":                #平均計算の際に邪魔なのでここで減らす
                value = int(values)
                #「1900,3200」など「，」でレアリティの区別をつけている際、前処理で,を消しているために「19003200」となってしまう
                #そのため、金額の上限を定めて回避する
                #また、一桁のデータが紛れ込むこともあるので回避
                if value < 999999:
                    if value > 10:
                        onlyValuesArray.append(value)

    return  onlyValuesArray


"""
平均計算
"""
def calcAve(data):
    sum = 0
    for value in data:
        print(value)
        sum += value
    return int(sum / len(data))


"""
初期設定
"""
CK = settings.CONSUMER_KEY
CS = settings.CONSUMER_SECRET
AT = settings.ACCESS_TOKEN
ATS = settings.ACCESS_TOKEN_SECRET
twitter = OAuth1Session(CK, CS, AT, ATS)

url = "https://api.twitter.com/1.1/search/tweets.json?tweet_mode=extended"

tweetlines = []     #抽出した文字群を入れる配列
results = []    #検索して一致したものを入れる配列
yugiohList = getCardList()


"""
入力に関する部分
"""
print("調べたいカード名を入力してください")
while True:
    checkWord = ""      #検索対象の名前を保存しておくため
    yesOrNo = ""
    keyword = input('>>')

    for cardName in yugiohList:
        if cardName.find(keyword) >= 0:
            print("「" + cardName + "」")
            checkWord = cardName
            break

    if checkWord != "":
        print("このカードでよろしいですか？")
        print("よろしければ「Y」、間違っていれば「N」を入力してください")
        yesOrNo = input('>>')

        if yesOrNo == "Y" or yesOrNo == "y" or yesOrNo == "Ｙ" or yesOrNo == "ｙ":
            print("検索を開始します")
            break

        elif yesOrNo == "N" or yesOrNo == "n" or yesOrNo == "Ｎ" or yesOrNo == "ｎ":
            print("再入力してください")

        else:
            print("無効な入力がありました")
            print("プログラムを終了します")
            sys.exit(0)

    else:
        print("一致する検索結果が見つかりませんでした")
        print("再入力してください")


"""
検索から除くレアリティを表す文字列を指定する
"""
arraysArray = []
arraysArray.append(raritysArray.yugiohSecret)
arraysArray.append(raritysArray.yugiohAsia)

pattern = r'('
for array in arraysArray:
    for rarity in array:
        pattern += '^' + rarity + '$'
        if rarity != array[-1]:
            pattern += '|'
pattern += ')'


"""
Twitterでの検索
"""
keyword = keyword + ' 買取 遊戯王 -rt'
params = {'q' : keyword, 'count' : 100}
req = twitter.get(url, params = params)

if req.status_code == 200:
    search_timeline = json.loads(req.text)

    """
    言語処理開始
    """
    t = Tokenizer(mmap=True)
    for tweet in search_timeline['statuses']:
        print('----------------------------------------------------')

        print(tweet['full_text'])
        tweet = tweet['full_text'].replace(",", "")
        splitedTweet = tweet.split('\n')     #ツイートを改行で分割

        #分割した文字列について回す
        for matchline in splitedTweet:
            lineAnalyze = t.tokenize(matchline)    #形態素解析を実行

            #抽出できた文字群を格納
            restoreArray = matchPieses(lineAnalyze)
            tweetlines.append(restoreArray)

    #一行ごとのカード名要素ごとにカードリストを検索
    for lines in tweetlines:
        checkResult = checkList(lines, yugiohList, 0)
        #存在していたら配列に加える
        if checkResult != 'not exist':
            results.append(checkResult)


    #確認用
    print('$----------------------------------------------------$')
    onlyValueArray = makeNewArrayOfValue(results, checkWord, pattern)
    print(checkWord + "の平均買取金額は"+ str(calcAve(onlyValueArray)) + "円です")
    print("また、最高値は" + str(max(onlyValueArray)) + "円です")
else:
    print("ERROR: %d" % req.status_code)