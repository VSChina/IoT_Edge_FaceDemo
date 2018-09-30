using System;

public static void getDoubleArray(string myIoTHubMessage, out double[][] feats, out string[] bboxs,out string frameIndex,ref TraceWriter log)
{
    string[] items = myIoTHubMessage.Split(',');
    string feat_string = "";
    string bbox_string = "";
    string frame_string = "";
    foreach(string item in items)
    {
        if(item.Contains("featureVectors"))
        {
            feat_string = item;
            continue;
        }
        if(item.Contains("rectIndex"))
        {
            bbox_string = item;
            continue;
        }
        if(item.Contains("frameIndex"))
        {
            frame_string = item;
            continue;
        }

    }

    frameIndex = frame_string.Split(':')[1].Trim().Trim('}').Trim('\"');
    string[] feat_strs = feat_string.Split(':')[1].Trim().Trim('}').Trim('\"').Split(new char[] { '&' },StringSplitOptions.RemoveEmptyEntries);
    bboxs = bbox_string.Split(':')[1].Trim().Trim('}').Trim('\"').Split(new char[] { '&' },StringSplitOptions.RemoveEmptyEntries);
    int face_count = feat_strs.Length;
    feats = new double[face_count][];
    for(int i = 0; i<face_count; ++i)
    {
        bboxs[i] = bboxs[i].Trim(']').Trim('[');
        feats[i] = feat_strs[i].Trim(']').Trim('[').Trim().Split(new char[] { ' ' },StringSplitOptions.RemoveEmptyEntries).Select(Double.Parse).ToArray();
    }
    
}

public static double calDistance(ref double[] feat_left, ref double[] feat_right)
{
    double distance = 0;
    int len = feat_left.Length;
    if(feat_right.Length!=len)
        return 100;
    for(int i = 0; i<len; ++i)
        distance += (feat_left[i]-feat_right[i])*(feat_left[i]-feat_right[i]);
    return distance;
}

public static string getIdentity(ref double[][] database,ref string[] persons,ref double[][] cur_feats,ref string[] bboxs,ref TraceWriter log)
{
    string res = "";
    double min_distance = 1.09;
    int face_count = cur_feats.Length;
    if(face_count == 0)
    {
        return res;
    }
    
    for(int i = 0; i<face_count; ++i)
    {
        double [] feat = cur_feats[i];
        string tmp_res = "Stranger";
        double cur_distance = min_distance;
        for(int j = 0; j<database.Length; ++j)
        {
            double person_distance = calDistance(ref database[j],ref feat);
            //log.Info($"{persons[j]}");
            //log.Info($"{person_distance}");
            if(person_distance < cur_distance)
            {
                cur_distance = person_distance;
                tmp_res = persons[j];
            }
        }
        //qiufan 223 445 444 667 stranger 223 445 667 888 ...
        res +=(tmp_res + "&" + bboxs[i] + "&");

    }
    res = res.Trim();
    return res;
}

public static void readDataBase(ref IEnumerable<dynamic> inputDocument, out double[][] database, out string[] persons)
{
    string onePerson;
    List<string> list = new List<string>();
    foreach (var doc in inputDocument)
    {
        onePerson = doc.name + ',' + doc.feature;
        list.Add(onePerson);
    }

    int len = list.Count;
    database = new double[len][];
    persons = new string[len];

    for(int i = 0; i<len; ++i)
    {
        string[] tmp = list[i].Split(',');
        persons[i] = tmp[0];
        database[i] = tmp[1].Trim().Split(new char[] { ' ' },StringSplitOptions.RemoveEmptyEntries).Select(Double.Parse).ToArray();
    }
}


public static string Run(string myIoTHubMessage, IEnumerable<dynamic> inputDocument, TraceWriter log)
{
    double[][] feats;
    string[] bboxs;
    double[][] database;
    string[] persons;
    string frameIndex;
    string res = "None";

    //log.Info($"C# IoT Hub trigger function processed a message: {myIoTHubMessage}");
    getDoubleArray(myIoTHubMessage,out feats, out bboxs,out frameIndex, ref log);
    readDataBase(ref inputDocument,out database, out persons);
    res = getIdentity(ref database, ref persons, ref feats,ref bboxs, ref log);
    res = frameIndex + "&" + res;
    log.Info($"{res}");
    return res;
}