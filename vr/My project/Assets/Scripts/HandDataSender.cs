using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

public class HandDataSender : MonoBehaviour
{
    public OVRSkeleton leftHandSkeleton;
    public OVRSkeleton rightHandSkeleton;

    private string apiUrl = "http://172.20.10.3:8000";  // Replace with your FastAPI URL

    void Start()
    {
        Debug.Log("🔄 Unity Started - Now sending ping...");
        StartCoroutine(PingServer()); // Check if server is reachable
    }

    void Update()
    {
        if (leftHandSkeleton != null && rightHandSkeleton != null)
        {
            // Capture hand data
            HandData handData = new HandData
            {
                leftHand = GetHandData(leftHandSkeleton),
                rightHand = GetHandData(rightHandSkeleton)
            };

            // Send hand data
            StartCoroutine(SendHandData(handData));
        }
    }

    private HandInfo GetHandData(OVRSkeleton skeleton)
    {
        List<Vector3Serializable> fingerPositions = new List<Vector3Serializable>();

        if (skeleton.Bones.Count > 0)
        {
            foreach (var bone in skeleton.Bones)
            {
                Vector3 position = bone.Transform.position;
                fingerPositions.Add(new Vector3Serializable(position));
            }
        }
        else
        {
            Debug.LogWarning("⚠️ OVRSkeleton has no bones - Hand tracking might not be initialized.");
        }

        return new HandInfo { fingers = fingerPositions };
    }

    private IEnumerator SendHandData(HandData handData)
    {
        string jsonData = JsonUtility.ToJson(handData);
        Debug.Log("📡 Sending Hand Data: " + jsonData);

        byte[] postData = System.Text.Encoding.UTF8.GetBytes(jsonData);
        UnityWebRequest request = new UnityWebRequest(apiUrl + "/save_hand_data", "POST");
        request.uploadHandler = new UploadHandlerRaw(postData);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

#if UNITY_ANDROID
        // Only needed for Android when using http://
        request.certificateHandler = new BypassCertificateHandler();
#endif

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ Hand data sent successfully: " + request.downloadHandler.text);
        }
        else
        {
            Debug.LogError("❌ Error sending hand data: " + request.error);
        }
    }

    private IEnumerator PingServer()
    {
        Debug.Log("🚀 PingServer() started in Unity!");

        UnityWebRequest request = UnityWebRequest.Get(apiUrl + "/ping");
        
#if UNITY_ANDROID
        // Only needed for Android when using http://
        request.certificateHandler = new BypassCertificateHandler();
#endif

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("✅ Server is reachable: " + request.downloadHandler.text);
        }
        else
        {
            Debug.LogError("❌ Cannot reach server: " + request.error);
        }
    }

    [System.Serializable]
    private class HandData
    {
        public HandInfo leftHand;
        public HandInfo rightHand;
    }

    [System.Serializable]
    private class HandInfo
    {
        public List<Vector3Serializable> fingers;
    }

    [System.Serializable]
    private struct Vector3Serializable
    {
        public float x, y, z;

        public Vector3Serializable(Vector3 vector)
        {
            x = vector.x;
            y = vector.y;
            z = vector.z;
        }
    }
}

public class BypassCertificateHandler : CertificateHandler
{
    protected override bool ValidateCertificate(byte[] certificateData)
    {
        return true;
    }
}





 
 