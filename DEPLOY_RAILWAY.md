# 🚀 Deploy to Railway - Step by Step Guide

**Perfect for weekly usage - 500 hours/month FREE!**

## 📋 **Pre-Deployment Checklist**

✅ **Security Ready:**
- [x] API key removed from code
- [x] `.gitignore` protects sensitive files  
- [x] Password protection enabled
- [x] Security headers implemented

✅ **Files Ready:**
- [x] `web_app.py` - Main application
- [x] `audio_transcriber.py` - Core functionality
- [x] `requirements.txt` - Dependencies
- [x] `railway.toml` - Railway configuration
- [x] `templates/` - HTML files
- [x] `.gitignore` - Security protection

---

## 🌐 **Step 1: Create Railway Account**

1. **Go to**: [railway.app](https://railway.app)
2. **Click**: "Start a New Project"
3. **Sign up**: With GitHub (recommended) or email
4. **Verify**: Your email if needed

---

## 📂 **Step 2: Upload Your Project**

### **Option A: GitHub (Recommended)**

**2.1 Create GitHub Repository:**
```bash
# In your project folder
git init
git add .
git commit -m "Audio transcriber with security"
```

Then:
1. Go to [github.com](https://github.com)
2. Click "New Repository"
3. Name: `audio-transcriber`
4. **Don't** check "Add README"
5. Click "Create repository"

**2.2 Push to GitHub:**
```bash
git remote add origin https://github.com/yourusername/audio-transcriber.git
git branch -M main
git push -u origin main
```

### **Option B: Direct Upload**
1. **Zip** your project folder
2. Upload directly to Railway

---

## ⚙️ **Step 3: Deploy on Railway**

**3.1 Create New Project:**
1. **Login** to Railway
2. **Click**: "New Project"
3. **Select**: "Deploy from GitHub repo" (if using GitHub)
4. **Choose**: Your `audio-transcriber` repository

**3.2 Configure Environment Variables:**
1. **Click**: Your deployed project
2. **Go to**: "Variables" tab
3. **Add** these variables:

```bash
OPENAI_API_KEY=your_new_openai_key_here
APP_PASSCODE=your_strong_password_here
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_ENV=production
```

**3.3 Generate Strong Secrets:**
- **FLASK_SECRET_KEY**: Use [random string generator](https://www.random.org/strings/)
- **APP_PASSCODE**: Strong password (12+ chars)
- **OPENAI_API_KEY**: Your new regenerated key

---

## 🔑 **Step 4: Set Up Your OpenAI Key**

**CRITICAL: Use a NEW API key**

1. **Go to**: [OpenAI API Keys](https://platform.openai.com/api-keys)
2. **Delete** old key: `sk-proj-Z_zzjkzDaPq...`
3. **Create** new key
4. **Copy** and add to Railway environment variables
5. **Set spending limit**: $10/month (safety)

---

## 🚀 **Step 5: Deploy!**

**5.1 Railway Auto-Deploy:**
- Railway automatically builds and deploys
- Wait 2-3 minutes for deployment
- Check the "Deployments" tab for progress

**5.2 Get Your URL:**
- **Click**: "Settings" → "Domains"
- **Click**: "Generate Domain"
- Your app URL: `https://your-app.railway.app`

---

## ✅ **Step 6: Test Your Deployment**

**6.1 Test Security:**
1. **Visit**: Your Railway URL
2. **Should see**: Login page (not main app)
3. **Enter**: Your APP_PASSCODE
4. **Should access**: Main transcriber interface

**6.2 Test Upload:**
1. **Upload**: A small audio file
2. **Enable**: Test mode (1 minute)
3. **Verify**: Transcription works
4. **Check**: OpenAI usage dashboard

---

## 💰 **Cost & Usage Monitoring**

### **Railway Free Tier:**
- ✅ **500 hours/month** (plenty for weekly use)
- ✅ **$5 monthly credit**
- ✅ **No sleep delays**
- ✅ **SSL/HTTPS included**

### **Monitor Usage:**
1. **Railway**: Check usage in dashboard
2. **OpenAI**: Monitor at [platform.openai.com/usage](https://platform.openai.com/usage)
3. **Set alerts**: For unusual usage

---

## 🔧 **Troubleshooting**

### **Common Issues:**

**❌ Build Failed:**
- Check `requirements.txt` format
- Verify Python version compatibility

**❌ App Won't Start:**
- Check environment variables are set
- Verify `railway.toml` configuration

**❌ Login Not Working:**
- Confirm `APP_PASSCODE` is set correctly
- Check Railway logs for errors

**❌ Transcription Fails:**
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI account has credits

### **Check Logs:**
1. **Railway Dashboard** → Your Project
2. **Click**: "View Logs"
3. **Look for**: Error messages

---

## 🎉 **Success! Your App is Live**

### **Share Your App:**
- **URL**: `https://your-app.railway.app`
- **Security**: Protected by your passcode
- **Usage**: Perfect for weekly transcriptions
- **Cost**: Completely FREE!

### **Next Steps:**
1. **Bookmark** your app URL
2. **Save** your passcode securely
3. **Monitor** OpenAI usage
4. **Enjoy** your secure transcriber!

---

## 📱 **Mobile Usage**

Your app is **fully mobile-optimized**:
- ✅ **Works on phones** and tablets
- ✅ **Touch-friendly** interface
- ✅ **File upload** from camera roll
- ✅ **Responsive** design

---

**Ready to deploy? Follow the steps above and you'll have your secure transcriber live in minutes!** 🚀