//
// Adrian Rosoga, Started March 2012, finished 25 March 2013 ;)
//
// E.g.: a.txt is versioned as a_v0.txt, a_v1.txt, etc.
//
#include <stdlib.h>
#include <iostream>
#include <string>
#include <boost/filesystem.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/regex.hpp>

using namespace std;
using namespace boost::filesystem;

// Checks whether the stem of the filename ends in _v(\\d+)
bool is_already_versioned(const string& filename_stem)
{
  boost::regex e(".*_v(\\d+)");
  boost::cmatch what;
      
  return boost::regex_match(filename_stem.c_str(), what, e);
}

// Goes through all the filenames in the directory, get the last versioned and returns the
// next version number to use
string get_version_to_use(const path& p, const path& stem, const path& extension)
{
  int max_version = -1;
  
  for (auto iter = directory_iterator(p); iter != directory_iterator(); ++iter)
  {
      const path& name = iter->path();
      
      if (name.extension() != extension) { continue; }
      
      boost::regex e(stem.native() + "_v(\\d+)");
      boost::cmatch what;
      
      if (boost::regex_match(name.stem().native().c_str(), what, e))
      {
        max_version = max(max_version, boost::lexical_cast<int>(what[1].str()));
      }
      
      //cout << name << endl;
  }
  
  return boost::lexical_cast<string>(max_version + 1);
}

int main(int argc, char **argv)
{
  if (argc != 2) {
    cerr << "Usage: " << argv[0] << " <filename>" << endl;
    cerr << "a.txt will be versioned as a_v0.txt, a_v1.txt, etc." << endl;
    return 1;
  }
    
  try {
    
    path p(argv[1]);
    
    if (!exists(p))
    {
      cerr << "Error: " << p << " does not exist!\n";
      return 1;
    }
    
    if (!is_regular_file(p))
    {
      cerr << "Error: " << p << " exists, but is not a file that can be versioned!\n";
      return 1; 
    }
    
    if (is_already_versioned(p.stem().native()))
    {
      cerr << "Error: This file is already versioned!" << endl;
      return 1;
    }
    string version, backup_file;
    
    // Hack to dealwith the case one gives or not a relative path
    if (string(argv[1]).find_first_of("/") == string::npos)
    {
      string version = get_version_to_use(path("."), p.stem(), p.extension());
                
      backup_file = p.stem().native() + "_v" +
                      version + p.extension().native();
    }
    else
    {
      version = get_version_to_use(p.parent_path().native() + "/", p.stem(), p.extension());
                
      backup_file = p.parent_path().native() + "/" + p.stem().native() + "_v" +
                            version + p.extension().native();
    }
    
    cout <<"New versioned file: " << backup_file << endl;
                
    copy(p, backup_file);
    
  }
  catch (const filesystem_error& ex)
  {
    cerr << "Error: Exception caught " << ex.what() << '\n';
    return 1;
  }
    
  return 0;
}
